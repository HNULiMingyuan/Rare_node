import random
import pyinputplus as pyip

class TestBench:
    def __init__(self, filename):
        self.filename = filename
        self.nodes = []
    
    def readnodes(self):
        with open(self.filename, 'r') as f:
            self.nodes = [line.strip() for line in f.readlines() if line.strip()]
        return self.nodes
    
    def getDut_nodes(self, rareNodes_num, sample_num):
        selected_combination = set()
        while len(selected_combination) < sample_num:
            num_nodes_to_select = random.randint(1, rareNodes_num)
            selected_nodes = tuple(sorted(random.sample(self.nodes, num_nodes_to_select)))
            selected_combination.add(selected_nodes)
        return selected_combination
            
def main():
    filename = pyip.inputStr(prompt="输入存储低活性节点的文件名称：low_activity_nodes.txt\n")
    rareNodes_num = pyip.inputNum(prompt="输入Trigger最多使用节点数：\n")
    sample_num = pyip.inputNum(prompt="输入采样数：\n")
    TB = TestBench(filename)
    TB.readnodes()
    Select_Nodes = TB.getDut_nodes(rareNodes_num, sample_num)
    
    output_file = "Sample_nodes.txt"
    with open(output_file, 'w') as f:
        for i in Select_Nodes:
            f.write(str(i) + '\n')
            print(i)

if __name__ == '__main__':
    main()

