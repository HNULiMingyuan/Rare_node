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

    # 生成10个周期的节点名称和对应的二进制值的映射，并写入input.txt
    with open(input_txt_path, 'w') as file:
        for i in range(1, 11):  # 生成cycle1到cycle10的两组二进制串
            for _ in range(5):  # 为每个周期生成两组数据
                node_binary_map = {node: random.choice(['0', '1']) for node in unique_nodes}
                binary_string = ''.join(node_binary_map.values())
                file.write(f"cycle{i}:{binary_string}\n")

    return node_binary_map


def update_testbench_file(input_txt_path, testbench_file_path, node_binary_map, cycle_number, delay):
    with open(input_txt_path, 'r') as file:
        input_lines = file.readlines()

    # 选取指定周期的两行
    cycle_lines = [line for line in input_lines if line.startswith(f"cycle{cycle_number}:")]

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
    for input_line in cycle_lines:
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

def analyze_saif_and_update_flip_count_file(saif_file, flip_count_file):
    with open(saif_file, 'r') as file:
        saif_lines = file.readlines()

    # 标记是否处于 "INSTANCE uut" 部分
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
            # 遇到新的 INSTANCE，表示离开了 uut 部分
            in_uut_instance = False

        if in_uut_instance and line.strip().startswith('(') and 'NET' not in line:
            node_name = line.split()[0].strip('(')
            if node_name.startswith(('G', 'g', 'I')):
                current_node = node_name
                if current_node not in nodes:
                    nodes.append(current_node)
                    node_flip_count[current_node] = '0'  # 初始化翻转次数为 0

        if in_uut_instance and '(TC' in line and current_node:
            tc_val = int(line.split('(TC ')[1].split(')')[0])
            node_flip_count[current_node] = str(tc_val)

    # 写入翻转次数文件
    # 清空 flip_count.txt 文件并写入新的翻转次数
    with open(flip_count_file, 'w') as file:
        for node, flip_count in node_flip_count.items():
            file.write(f"{node} {flip_count}\n")


def main_loop(verilog_file_path, testbench_file_path, input_txt_path, output_txt_path, saif_file_path, flip_count_file, verilog_directory):
    delay_flip_probabilities = {}  # 存储不同延迟值的平均翻转率
    cycle_delay_flip_probabilities = {}  # 存储每个周期在每个延迟下的翻转率

    # 仅生成一次输入文件
    binary_node_map = extract_and_generate_binary(verilog_file_path, input_txt_path)

    for delay in range(20, 301, 20):  # 对每个延迟值进行循环
        flip_probabilities = []
        for cycle in range(1, 11):  # 对每个周期进行循环
            # 清理旧数据
            clear_old_data(output_txt_path, low_activity_txt_path, flip_count_file)

            # 使用相同的输入文件更新testbench文件
            update_testbench_file(input_txt_path, testbench_file_path, binary_node_map, cycle, delay)

            # 运行VCS并计算翻转率
            run_vcs(verilog_directory, verilog_file_path, testbench_file_path)
            analyze_saif_and_update_flip_count_file(saif_file_path, flip_count_file)
            flip_prob = calculate_flip_probability(flip_count_file)

            # 存储每个周期在每个延迟下的翻转率
            if cycle not in cycle_delay_flip_probabilities:
                cycle_delay_flip_probabilities[cycle] = {}
            cycle_delay_flip_probabilities[cycle][delay] = flip_prob

            flip_probabilities.append(flip_prob)

        # 计算并存储当前延迟值的平均翻转率
        average_flip_probability = sum(flip_probabilities) / len(flip_probabilities)
        delay_flip_probabilities[delay] = average_flip_probability

    return delay_flip_probabilities, cycle_delay_flip_probabilities



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
def clear_old_data(output_txt_path, low_activity_txt_path, flip_count_file):
    open(output_txt_path, 'w').close()
    open(low_activity_txt_path, 'w').close()
    open(flip_count_file, 'w').close()

def calculate_flip_probability(flip_count_file):
    with open(flip_count_file, 'r') as file:
        lines = file.readlines()

    # 初始化节点总数和翻转次数不为零的节点数
    total_nodes = 0
    non_zero_flip_nodes = 0

    for line in lines:
        flips = line.split()
        for i in range(0, len(flips), 2):  # 跳过节点名称，只读取翻转次数
            count = int(flips[i + 1])
            total_nodes += 1
            if count != 0:
                non_zero_flip_nodes += 1

    # 计算翻转概率
    if total_nodes == 0:
        return 0  # 避免除以零
    flip_probability = non_zero_flip_nodes / total_nodes
    return flip_probability


# 定义测试次数和总周期数
test_times = 1  # 可以根据需要更改
total_cycles = 20 * test_times
repeat_times = 20  # 重复运行测试的次数

# 文件路径（根据您的文件位置更新这些路径）
verilog_file_path = 'c880.v'
testbench_file_path = 'tb_c880.v'
input_txt_path = 'input.txt' 
output_txt_path = 'output.txt'  # 输出文件路径
saif_file_path = 'c880.saif'  # SAIF文件路径
verilog_directory = '.'  # 定义Verilog文件所在的目录
low_activity_txt_path = 'low_activity_nodes.txt'  # 低活性节点输出文件路径
flip_count_file = 'flip_count.txt'  # 翻转次数文件路径

# 执行主循环
delay_flip_probabilities, cycle_delay_flip_probabilities = main_loop(
    verilog_file_path, testbench_file_path, input_txt_path, 
    output_txt_path, saif_file_path, flip_count_file, verilog_directory
)

# 打印每个延迟值的平均翻转率
print("平均翻转率（各延迟）:")
for delay, flip_prob in delay_flip_probabilities.items():
    print(f"  延迟 {delay}: {flip_prob}")

# 打印每个周期在每个延迟下的翻转率
print("\n每个周期在各延迟下的翻转率:")
for cycle, delays in cycle_delay_flip_probabilities.items():
    print(f"  {cycle}:")
    for delay, flip_prob in delays.items():
        print(f"    延迟 {delay}: {flip_prob}")

