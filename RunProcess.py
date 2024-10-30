import os
import re
import shutil

class Run:
    '''
    根据测试覆盖率结果分析覆盖率情况，筛选种集，种集权重赋值
    '''

    def __init__(self) -> None:
        pass

    def update_testbench(self, testbench_file, input_file):
        # 读取测试平台文件以提取输入端口名称
        with open(testbench_file, 'r') as file:
            tb_lines = file.readlines()

        input_ports = []
        for line in tb_lines:
            if line.strip().startswith('reg '):
                # 处理可能跨越多行的定义
                while ';' not in line:
                    next_line = next(file).strip()
                    line += next_line
                ports_str = line.split('reg ')[1]
                ports_str = ports_str.split(';')[0]  # 移除行尾的分号
                ports = [port.strip() for port in ports_str.split(',')]
                input_ports.extend(ports)

        # 移除CK端口
        if 'CK' in input_ports:
            input_ports.remove('CK')
        if 'VDD' in input_ports:
            input_ports.remove('VDD')
        if 'GND' in input_ports:
            input_ports.remove('GND')

        # 读取输入文件并分析每个周期的值
        with open(input_file, 'r') as file:
            input_lines = file.readlines()

        start_index = next(i for i, line in enumerate(tb_lines) if '$toggle_start;' in line) + 1
        stop_index = next(i for i, line in enumerate(tb_lines) if '$toggle_stop;' in line)

        new_tb_lines = tb_lines[:start_index]
        for input_line in input_lines:
            if ':' not in input_line:
                continue
            _, values = input_line.strip().split(':')
            values = values.strip()
            if len(values) == len(input_ports):
                for i, val in enumerate(values):
                    new_tb_lines.append(f"        {input_ports[i]} = 1'b{val};\n")
                new_tb_lines.append("        #20;\n")
        new_tb_lines.extend(tb_lines[stop_index:])

        # 写回修改后的测试平台文件
        with open(testbench_file, 'w') as file:
            file.writelines(new_tb_lines)

    def run_vcs(self, verilog_directory, verilog_file_path, testbench_file_path):
        os.chdir(verilog_directory)
        os.system(f'vcs -j50 -full64 -sverilog -debug_all -timescale=1ns/1ps {verilog_file_path} {testbench_file_path} ')
        os.system('./simv ')

    def analyze_saif_and_update_flip_file(self, saif_file, flip_file):
        with open(saif_file, 'r') as file:
            content = file.read()

        # 使用正则表达式提取 "INSTANCE uut" 部分
        uut_part_match = re.search(r'\(INSTANCE uut(.*?)\)\s*\)\s*\)', content, re.DOTALL)
        if uut_part_match:
            uut_part = uut_part_match.group(1)
        else:
            uut_part = ''  # 如果没有匹配到，设置为空字符串

        nodes = []

        # 在 "INSTANCE uut" 部分提取电路节点名称，忽略GND、VDD和CK，且仅包含以 'G' 或 'I' 开头的节点
        for line in uut_part.splitlines():
            if line.strip().startswith('(') and 'NET' not in line:
                node_name = line.split()[0].strip('(')
                if node_name.startswith(('G', 'g', 'I')) and node_name not in ['GND', 'VDD', 'CK']:
                    nodes.append(node_name)

        flip_status = {node: '0' for node in nodes}  # 初始化翻转状态

        # 在 "INSTANCE uut" 部分提取翻转状态，忽略VDD、GND和CK
        current_node = None
        for line in uut_part.splitlines():
            if line.strip().startswith('(') and 'NET' not in line:
                node_name = line.split()[0].strip('(')
                if node_name in nodes:
                    current_node = node_name
                elif node_name in ['GND', 'VDD', 'CK']:
                    continue  # 忽略GND、VDD和CK

            if '(TC' in line and current_node:
                tc_val = int(line.split('(TC ')[1].split(')')[0])
                flip_status[current_node] = '1' if tc_val > 0 else '0'

        flips = ''.join(flip_status[node] for node in nodes)

        # 更新 flip 文件
        test_num = 1
        if os.path.exists(flip_file):
            with open(flip_file, 'r') as file:
                for line in file:
                    if line.startswith("Test"):
                        test_num += 1

        if not os.path.exists(flip_file):
            with open(flip_file, 'w') as file:
                file.write("Node flipping number\n")
                file.write(' '.join(nodes) + '\n')

        with open(flip_file, 'a') as file:
            file.write(f"Test{test_num}    {flips}\n")



    def writeInput(self, input, input_filename):
        with open(input_filename, 'w') as f:
            for x,i in enumerate(input):
                f.write("cycle"+str(x+1)+":"+str(i)+"\n")

    def analyze_saif_and_update_flip_count_file(self, saif_file, flip_count_file):
        with open(saif_file, 'r') as file:
            saif_lines = file.readlines()

        # 标记是否处于"INSTANCE uut"部分
        in_uut_instance = False

        # 提取所有电路节点名称及其翻转次数
        nodes = []
        node_flip_count = {}
        current_node = None
        for line in saif_lines:
            if line.strip() == '(INSTANCE uut':
                in_uut_instance = True
                continue
            elif in_uut_instance and line.strip().startswith('(INSTANCE'):
                # 遇到新的INSTANCE，表示离开了uut部分
                in_uut_instance = False

            if in_uut_instance and line.strip().startswith('(') and 'NET' not in line:
                node_name = line.split()[0].strip('(')
                if node_name.startswith(('G', 'g', 'I')):
                    current_node = node_name
                    if current_node not in nodes:
                        nodes.append(current_node)
                        node_flip_count[current_node] = '0'  # 初始化翻转次数为0

            if in_uut_instance and '(TC' in line and current_node:
                tc_val = int(line.split('(TC ')[1].split(')')[0])
                node_flip_count[current_node] = str(tc_val)

        # 确定测试编号
        test_num = 1
        if os.path.exists(flip_count_file):
            with open(flip_count_file, 'r') as file:
                for line in file:
                    if line.startswith("Test"):
                        test_num += 1

        # 写入或更新翻转次数文件
        if not os.path.exists(flip_count_file):
            with open(flip_count_file, 'w') as file:
                file.write("Node flipping number\n")

        with open(flip_count_file, 'a') as file:
            flip_count_str = ' '.join([f"{node} {node_flip_count[node]}" for node in nodes])
            file.write(f"Test{test_num} {flip_count_str}\n")

    @staticmethod
    def read_nodes(file_path):
        with open(file_path, 'r') as file:
            return [eval(line.strip()) for line in file]
    @staticmethod
    def extract_tc_values(saif_file, nodes):
        with open(saif_file, 'r') as file:
            saif_content = file.read()
    
        tc_values = {}
        for node in nodes:
            node_pattern = r'\(\s*{}\s+'.format(re.escape(node))
            node_match = re.search(node_pattern, saif_content, re.MULTILINE)
            if node_match:
                tc_pattern = r'\(TC (\d+)\)'
                tc_match = re.search(tc_pattern, saif_content[node_match.end():], re.MULTILINE)
                if tc_match:
                    tc_values[node] = int(tc_match.group(1))
                    print(f"Found TC value for {node}: {tc_values[node]}")  # 打印找到的TC值
                else:
                    print(f"No TC value found for {node}")  # 如果没有找到TC值，打印提示
            else:
                print(f"No node found for {node}")  # 如果没有找到节点，打印提示

        return tc_values

    @staticmethod
    def copy_if_conditions_met(saif_file, node_groups, input_file, output_file):
        all_nodes = [node for group in node_groups for node in group]
        tc_values = Run.extract_tc_values(saif_file, all_nodes)  # Run.extract_tc_values调用

        for group in node_groups:
            if all(tc_values.get(node, 0) != 0 for node in group):
                print(f"All TC values for group {group} are not zero. Updating {output_file}.")
                with open(output_file, 'a') as out_file:
                    out_file.write(str(group) + '\n')
                    shutil.copyfileobj(open(input_file, 'r'), out_file)
                    out_file.write('\n')
            else:
                print(f"Not all TC values for group {group} are non-zero. Skipping update.")


    def analyze_saif_and_update_monitor_nodes_file(self, saif_file, monitor_nodes_file, sample_nodes_file, new_file):
        if not os.path.exists(new_file):
            with open(sample_nodes_file, 'r') as original, open(new_file, 'w') as new_file_writer:
                for line in original:
                    new_file_writer.write(line.strip() + "\n0\n") 

        with open(saif_file, 'r') as file:
            saif_lines = file.readlines()

        in_uut_instance = False

        node_flip_count = {}
        current_node = None
        for line in saif_lines:
            if line.strip() == '(INSTANCE uut':
                in_uut_instance = True
                continue
            elif in_uut_instance and line.strip().startswith('(INSTANCE'):
                in_uut_instance = False

            if in_uut_instance and line.strip().startswith('(') and 'NET' not in line:
                node_name = line.split()[0].strip('(')
                if node_name.startswith(('G', 'g', 'I')):
                    current_node = node_name
                    node_flip_count[current_node] = 0

                if in_uut_instance and '(TC' in line and current_node:
                    tc_val = int(line.split('(TC ')[1].split(')')[0])
                    node_flip_count[current_node] = tc_val

        with open(new_file, 'r') as file:
            lines = file.readlines()

        updated_lines = []
        one_count = 0  
        zero_count = 0 

        for i in range(0, len(lines) - 1, 2): 
            node_line = lines[i].strip()
            count_line = lines[i + 1].strip()

            nodes_in_group = eval(node_line) if node_line else ()
            if count_line == "0" and all(node_flip_count.get(node.strip(), 0) != 0 for node in nodes_in_group):
                updated_count_line = "1"
                one_count += 1
            else:
                updated_count_line = count_line
                if updated_count_line == "0":
                    zero_count += 1
                elif updated_count_line == "1":
                    one_count += 1

            updated_lines.append(node_line + "\n")
            updated_lines.append(updated_count_line + "\n")

        rate = one_count / (zero_count + one_count) if (zero_count + one_count) > 0 else 0
        updated_lines.append(f"rate={rate}\n")

        with open(new_file, 'w') as file:
            file.writelines(updated_lines)



    def runProcess(self, input):
        verilog_directory = '.'  # Verilog directory path
        verilog_file_path = 'c880.v'
        testbench_file_path = 'tb_c880.v'  # Testbench file name
        input_file = 'input.txt'  # Input file name
        saif_file = 'c880.saif'  # SAIF file name
        flip_file = 'node_flipping.txt'  # Flip file name
        flip_count_file = 'flip_count.txt'
        output_file = 'out.txt'  # Output file name
        sample_nodes_file = 'Sample_nodes.txt'  # Sample nodes file name
        monitor_nodes_file = 'monitor_nodes.txt'    # monitor nodes tc value   
        new_file = 'new.txt'

        # Step 1: Write input
        self.writeInput(input, input_file)

        # Step 2: Update testbench and run vcs
        self.update_testbench(testbench_file_path, input_file)
        self.run_vcs(verilog_directory, verilog_file_path, testbench_file_path)

        # Step 3: Analyze SAIF and copy contents if conditions met
        node_groups = Run.read_nodes(sample_nodes_file)
        self.copy_if_conditions_met(saif_file, node_groups, input_file, output_file)

        # Step 4: Analyze SAIF file and update flip files
        self.analyze_saif_and_update_flip_file(saif_file, flip_file)
        self.analyze_saif_and_update_flip_count_file(saif_file, flip_count_file)
        self.analyze_saif_and_update_monitor_nodes_file(saif_file, monitor_nodes_file, sample_nodes_file,new_file)
        with open('new.txt', 'r') as file:
            lines = file.readlines()
            if lines and lines[-1].startswith('rate='):
                return float(lines[-1].split('=')[1])
            else:
                return 0
