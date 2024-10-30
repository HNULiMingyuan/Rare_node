import re

def extract_verilog_nodes(verilog_file):
    # 定义过滤掉的节点名称
    exclude_names = {'GND', 'VDD', 'CK'}

    # 定义正则表达式匹配 input、wire 和 output 后面的节点名称
    pattern = re.compile(r'\b(input|output|wire)\b\s*([\w,\s]+)\;')

    # 使用正则表达式找到所有匹配项
    nodes_set = set()
    with open(verilog_file, 'r') as f:
        verilog_text = f.read()

    matches = pattern.findall(verilog_text)

    # 提取节点名称并过滤
    for match in matches:
        # 第二个捕获组包含了节点名称，按逗号分割
        nodes = match[1].replace('\n', '').split(',')
        # 去除两端空格并添加到节点集合中，除非是要排除的节点名称
        nodes_set.update(node.strip() for node in nodes if node.strip() not in exclude_names)

    # 返回所有找到的节点名称的列表
    return sorted(nodes_set)



verilog_file = 'c880.v'
nodes = extract_verilog_nodes(verilog_file)
print(nodes)
print(len(nodes))