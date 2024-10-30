import re
import os
import random

def extract_and_generate_binary(verilog_file_path, input_txt_path):
    # 读取.verilog文件
    with open(verilog_file_path, 'r') as file:
        content = file.read()

    # 从每个输入声明中提取以'g''G'或'I'开头的输入节点
    input_nodes = []
    input_declarations = re.findall(r'input\s+.*?;', content, re.DOTALL)
    for decl in input_declarations:
        input_nodes += re.findall(r'\b[g|G|I]\d+\b', decl)

    # 移除重复项并排序
    unique_nodes = sorted(set(input_nodes), key=lambda x: (x[0], int(re.search(r'\d+', x).group())))

    # 生成节点名称和对应的二进制值的映射
    node_binary_map = {node: random.choice(['0', '1']) for node in unique_nodes}
    binary_string = ''.join(node_binary_map.values())

    # 将二进制字符串写入input.txt
    with open(input_txt_path, 'w') as file:
        file.write(f"cycle1:{binary_string}")

    return node_binary_map

def update_testbench_file(input_txt_path, testbench_file_path, node_binary_map):
    # 读取input.txt文件
    with open(input_txt_path, 'r') as file:
        input_data = file.read().strip()

    # 提取'cycle1:'后的二进制字符串
    binary_values = input_data.split(':')[1]

    # 读取tb_s.v文件
    with open(testbench_file_path, 'r') as file:
        testbench_file_content = file.readlines()

    # 找到插入的起始和结束索引
    start_index, stop_index = -1, -1
    for i, line in enumerate(testbench_file_content):
        if "$toggle_start;" in line:
            start_index = i + 1
        if "$toggle_stop;" in line:
            stop_index = i
            break

    if start_index == -1 or stop_index == -1:
        print("文件中未找到插入点。")
        return

    # 准备插入的字符串
    assignment_lines = []
    for node, bit in node_binary_map.items():
        assignment_lines.append(f"        {node} = {bit};\n")

    assignment_lines.append("        #20;\n")  # 添加延迟语句

    # 将赋值插入到tb_s_file内容中
    testbench_file_content[start_index:stop_index] = assignment_lines

    # 将更新后的内容写回tb_s.v
    with open(testbench_file_path, 'w') as file:
        file.writelines(testbench_file_content)

def run_vcs(verilog_directory, verilog_file_path, testbench_file_path):
    os.chdir(verilog_directory)
    os.system(f'vcs -full64 -sverilog -debug_all -timescale=1ns/1ps {verilog_file_path} {testbench_file_path} -l compile.log')
    os.system('./simv -l simulation.log')

def parse_saif_and_accumulate(saif_file_path, output_txt_path):
    # 读取SAIF文件内容
    with open(saif_file_path, 'r') as file:
        content = file.read()

    # 提取“INSTANCE uut”部分
    uut_part = re.search(r'\(INSTANCE uut(.*?)\)\s*\)\s*\)\s*\)', content, re.DOTALL)


    if not uut_part:
        print("未找到 INSTANCE uut 部分")
        return

    # 提取所有相关节点及其T0和T1值
    pattern = r'\((g\d+|G\d+|I\d+).*?\(T0 (\d+)\) \(T1 (\d+)\)'
    nodes_data = re.findall(pattern, uut_part.group(1), re.DOTALL)

    # 检查输出文件是否存在并读取之前的累加结果
    if os.path.exists(output_txt_path):
        with open(output_txt_path, 'r') as output_file:
            existing_data = {}
            for line in output_file:
                parts = line.split()
                if len(parts) == 3:
                    node = parts[0]
                    t0 = int(parts[1].split('=')[1])
                    t1 = int(parts[2].split('=')[1])
                    existing_data[node] = [t0, t1]

    else:
        existing_data = {}

    # 累加数据
    for node, t0, t1 in nodes_data:
        if node in existing_data:
            existing_data[node][0] += int(t0)
            existing_data[node][1] += int(t1)
        else:
            existing_data[node] = [int(t0), int(t1)]

    # 写入更新后的数据到输出文件
    with open(output_txt_path, 'w') as output_file:
        for node, counts in existing_data.items():
            output_file.write(f"{node} T0={counts[0]} T1={counts[1]}\n")

def main_loop(verilog_file_path, testbench_file_path, input_txt_path, output_txt_path, saif_file_path, verilog_directory, test_times):
    for _ in range(test_times):
        binary_node_map = extract_and_generate_binary(verilog_file_path, input_txt_path)
        update_testbench_file(input_txt_path, testbench_file_path, binary_node_map)
        run_vcs(verilog_directory, verilog_file_path, testbench_file_path)
        parse_saif_and_accumulate(saif_file_path, output_txt_path)

def find_low_activity_nodes(output_txt_path, low_activity_txt_path, total_cycles):
    low_activity_nodes = []

    with open(output_txt_path, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) == 3:
                node = parts[0]
                t0 = int(parts[1].split('=')[1])
                t1 = int(parts[2].split('=')[1])

                # 计算T0和T1的比例
                t0_ratio = t0 / total_cycles
                t1_ratio = t1 / total_cycles

                if t0_ratio > 0.9 or t1_ratio > 0.9:
                    low_activity_nodes.append(node)

    # 将低活性节点写入新的文本文件
    with open(low_activity_txt_path, 'w') as file:
        for node in low_activity_nodes:
            file.write(f"{node}\n")

# 清理旧文件
def clear_old_data(output_txt_path, low_activity_txt_path):
    open(output_txt_path, 'w').close()
    open(low_activity_txt_path, 'w').close()

# 定义测试次数和总周期数
test_times = 100000  # 可以根据需要更改
total_cycles = 20 * test_times

# 文件路径（根据您的文件位置更新这些路径）
verilog_file_path = 'c880.v'
testbench_file_path = 'tb_c880.v'
input_txt_path = 'input.txt' 
output_txt_path = 'output.txt'  # 输出文件路径
saif_file_path = 'c880.saif'  # SAIF文件路径
verilog_directory = '.'  # 定义Verilog文件所在的目录
low_activity_txt_path = 'low_activity_nodes.txt'  # 低活性节点输出文件路径

# 清理旧数据
clear_old_data(output_txt_path, low_activity_txt_path)

# 执行主循环
main_loop(verilog_file_path, testbench_file_path, input_txt_path, output_txt_path, saif_file_path, verilog_directory, test_times)
find_low_activity_nodes(output_txt_path, low_activity_txt_path, total_cycles)
