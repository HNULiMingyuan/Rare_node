import random
import re
import os
import time


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

    # 随机生成周期数，范围从1到50
    num_cycles = random.randint(1, 50)

    # 生成随机周期数的节点名称和对应的二进制值的映射，并写入input.txt
    with open(input_txt_path, 'w') as file:
        for i in range(1, num_cycles + 1):  # 生成随机周期数的二进制串
            node_binary_map = {node: random.choice(['0', '1']) for node in unique_nodes}
            binary_string = ''.join(node_binary_map.values())
            file.write(f"cycle{i}:{binary_string}\n")

    return node_binary_map

def update_testbench_file(input_txt_path, testbench_file_path, delay):
    with open(input_txt_path, 'r') as file:
        input_lines = file.readlines()

    with open(testbench_file_path, 'r') as file:
        testbench_file_content = file.readlines()

    # 找到插入的起始和结束索引
    start_index, stop_index = -1, -1
    for i, line in enumerate(testbench_file_content):
        if "$toggle_start;" in line:
            start_index = i + 1
        elif "$toggle_stop;" in line:
            stop_index = i
            break

    if start_index == -1 or stop_index == -1:
        print("文件中未找到插入点。")
        return

    # 准备插入的字符串
    insertion_lines = []
    for input_line in input_lines:
        if input_line.startswith("cycle"):
            _, binary_values = input_line.strip().split(':')
            for node, bit in zip(node_binary_map.keys(), binary_values):
                insertion_lines.append(f"        {node} = {bit};\n")
            insertion_lines.append(f"        # {delay};\n")  # 添加延迟

    # 替换testbench文件中指定区域的内容
    testbench_file_content = testbench_file_content[:start_index] + insertion_lines + testbench_file_content[stop_index:]

    # 将更新后的内容写回testbench文件
    with open(testbench_file_path, 'w') as file:
        file.writelines(testbench_file_content)


def run_vcs(verilog_directory, verilog_file_path, testbench_file_path):
    os.chdir(verilog_directory)
    os.system(f'vcs -full64 -sverilog -debug_all -timescale=1ns/1ps {verilog_file_path} {testbench_file_path} -l compile.log')
    os.system('./simv -l simulation.log')

def analyze_saif_and_update_monitor_nodes_file(saif_file, monitor_nodes_file, sample_nodes_file, new_file):
    # 检查并初始化新文件
    if not os.path.exists(new_file):
        with open(sample_nodes_file, 'r') as original, open(new_file, 'w') as new_file_writer:
            for line in original:
                new_file_writer.write(line.strip() + "\n0\n") 

    # 读取SAIF文件内容
    try:
        with open(saif_file, 'r') as file:
            saif_lines = file.readlines()
    except IOError as e:
        print(f"读取SAIF文件时发生错误: {e}")
        return

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

    # 读取并更新新文件
    try:
        with open(new_file, 'r') as file:
            lines = file.readlines()
    except IOError as e:
        print(f"读取新文件时发生错误: {e}")
        return

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

    try:
        with open(new_file, 'w') as file:
            file.writelines(updated_lines)
    except IOError as e:
        print(f"写入新文件时发生错误: {e}")

# 文件路径（根据文件位置更新这些路径）
verilog_file_path = 'c880.v'
testbench_file_path = 'tb_c880.v'
input_txt_path = 'input.txt'
verilog_directory = '.'  # 定义Verilog文件所在的目录
saif_file = 'c880.saif'
monitor_nodes_file = 'monitor_nodes.txt'
sample_nodes_file = 'Sample_nodes.txt'
new_file = 'new.txt'

# 定义延迟值
delay = 20  # 可以根据需要更改这个值

end_time = time.time() + 10 * 3600  # 10小时转换为秒

while time.time() < end_time:
    # 调用 extract_and_generate_binary 函数生成 input.txt 并获取节点映射
    node_binary_map = extract_and_generate_binary(verilog_file_path, input_txt_path)

    # 使用生成的节点映射和 input.txt 文件内容更新 testbench 文件
    update_testbench_file(input_txt_path, testbench_file_path, delay)

    # 编译和运行 Verilog 代码
    run_vcs(verilog_directory, verilog_file_path, testbench_file_path)

    # 分析SAIF文件并更新监控节点文件
    analyze_saif_and_update_monitor_nodes_file(saif_file, monitor_nodes_file, sample_nodes_file, new_file)


# 脚本运行完成
print("脚本运行10小时已完成。")





