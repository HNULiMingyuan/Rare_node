'''
此文件包含所有与产生测试向量有关的函数

'''
import random
import secrets
import re
import numpy as np

#类高斯分布函数（分布对称，左右两边无限延伸，中间高两边低）
def gaussian_distribution(x, mean, std_dev):
    return 10*(1.0 / (np.sqrt(2 * np.pi) * std_dev)) * np.exp(-0.5 * ((x - mean) / std_dev) ** 2)

def flip_bit(bit):
    return '0' if bit == '1' else '1'

def mutate_singleInput(input_data, mean, std_dev):
        bit_string = ''.join(format(byte, '08b') for byte in input_data)
        flipped_bits = ''
        for i, bit in enumerate(bit_string):
    # 计算这一位的翻转概率
            flip_probability = gaussian_distribution(i, mean, std_dev)
    # 按照计算出的概率翻转位
            flipped_bits += flip_bit(bit) if random.random() < flip_probability else bit
        mutated_bytes = bytes(int(flipped_bits[i:i+8], 2) for i in range(0, len(flipped_bits), 8))
        return mutated_bytes


class Gen:
    '''
    产生测试数据
    '''
    def __init__(self) -> None:
        # self.inputleft_max = 20             #对大输入input_left数目
        # self.inputbytes_max = 24        #最大输入bytes数目 ，更换benchmark需要更改
        self.funcMap = {
            0: self.mutate_method0,
        }
        self.methodNum = len(self.funcMap)

    def getInitial_Seedset(self, inputSize):
            input_left = random.randint(1,10)  #随机测试数据初始最多每次测试选择10轮
            input = [None] * input_left
            seedset = {}
            for i in range(input_left):
                random_binary = ''.join(random.choice('01') for _ in range(inputSize))
                input[i] = random_binary
            seedset[tuple(input)] = 1   #赋初始权重值为1
            return seedset
    
    def get_input_seed(self, seedset):
        sorted_dict = sorted(seedset.items(),key = lambda item: item[1], reverse = True)  
        data = sorted_dict[:1]   #取权值最大的为突变种子
        a = dict(data)
        for key in a.keys():
            input_seed = key
        return input_seed
    
    def getIntermediate_states(self, Input_size):
        intermediates_states = [None] * Input_size
        intermedia_binary = ''.join(random.choice('0') for _ in range(Input_size))
        for i in range(len(intermediates_states)):
            list_data = list(intermedia_binary)
            list_data[i] = '1'
            intermediates_states[i] = ''.join(list_data)  
        return intermediates_states

    #计算某一个低活性节点在一次运行中被激活的次数
    #rare_nodes为字典类型变量，键为低活性节点，值为低活性节点被激活的次数
    def update_times(self, rare_nodes, rare_values, outputfile):
        change_flag = False
        with open(outputfile, 'r') as f:
            lines = f.readlines()
        
        filtered_rare_nodes = {}  # 创建一个新的空字典用于存储符合条件的键值对
        # 遍历原字典，筛选出满足条件的键值对，然后存入新字典中
        for key, value in rare_nodes.items():
            #只要低活性节点的翻转value有增加就行
            filtered_rare_nodes[key] = value

        for n in filtered_rare_nodes.keys():
            if rare_values[n] == 1:
                TC_message = re.compile(r'.*T1\s(\d+)*.')
            elif rare_values[n] == 0:
                TC_message = re.compile(r'.*T0\s(\d+)*.')
            flag = 0
            node_id = n
            node_message = r'.*\(' + re.escape(node_id) + r'.*'
            nodes = re.compile(node_message)
            for x,line in enumerate(lines):
                if nodes.search(line):
                    flag = x + 1
                    TC = int(TC_message.search(lines[flag]).group(1))/20    #一个周期是20个时间单位，满足一次rare value最少是一个周期
                    if TC > rare_nodes[n]:
                        rare_nodes[n] = TC
                        change_flag = True
                        break
        return rare_nodes, change_flag

    #判断是否增加了覆盖率
    def Judge_coverage(self, coverageMessage, totalCoverage):
        flag = 0
        for i in range(len(totalCoverage)):
            if int(totalCoverage[i]) == 0 and int(coverageMessage[i]) == 1:
                flag = 1
            else:
                flag = 0
        return flag
        

    #更新种集函数
    def update_seedset(self, seed_data, input_data, seedset, coverage_message, totalCoverage, rare_nodes, rare_values, outputfile):
        coverage_state = self.Judge_coverage(coverage_message, totalCoverage)
        new_rarenodes, rareNodes_state = self.update_times(rare_nodes, rare_values, outputfile)
        if coverage_state or rareNodes_state:
            seedset[seed_data] += 10   #可以增加覆盖率的种子增加优先度，提高容错率
            seedset[tuple(input_data)] = 1    #增加初始种子的容错度
        else:
            seedset[seed_data] -= 1
        new_seedset = {}
        for key,value in seedset.items():
            new_seedset[key] = value
        return new_seedset, new_rarenodes
    
# '''
# t突变方法部分需要更改的内容：
# 不从种集库中随机选择单轮的种子进行突变，将每次测试的一组数据作为一个种子进行突变（思考如何突变？是否每个bytes都需要突变？）
# 更改input_left时，每次突变选择加一，减一、不变，不要随机选择input_left，这样不合理
# '''

#——————————————————————已完成—————————————————————————————、
#input_seed为列表数据类型
##将突变种子选择权重最高的种子进行突变

#随机突变
    def mutate_method0(self, input_seed):
        if len(input_seed) <= 1:
            input_left_change = random.randint(0,1)
        else:
            weights = [0.9] *3 + [0.1] * 9
            # 随机选择一个数字
            input_left_change = random.choices(range(-1, 11), weights=weights)[0] 
        
        new_input = [None] * (int(input_left_change)+len(input_seed))
        if len(new_input) > len(input_seed):
            for n in range(len(input_seed)):
                new_input[n] = input_seed[n]
            size = len(input_seed[0])
            for j in (range(len(new_input)-len(input_seed))):
                random_binary = ''.join(random.choice('01') for _ in range(size))
                new_input[-(j+1)] =  random_binary
        else:
            #new_input = input_seed[:len(new_input)]
            for i in range(len(new_input)):
                new_input[i] = input_seed[i]
        for i in range(len(new_input)):
            position_length = random.randint(1,len(new_input[0]))
            position_list = [random.randint(0, len(new_input[0])-1) for _ in range(position_length)]
            print(position_list)
            for x in position_list:
                list_data = list(new_input[i])
                list_data[x] = str((int(new_input[i][x])+1) % 2)
                new_input[i] = ''.join(list_data)   #取反
        return new_input
    
    def mutate_method1(self, input_seed):
        if len(input_seed) <= 1:
            input_left_change = random.randint(0,1)
        else:
            # 随机选择一个数字
            input_left_change = random.randint(-1,1)
        new_input = [None] * (int(input_left_change)+len(input_seed))
        
        if len(new_input) > len(input_seed):
            for n in range(len(input_seed)):
                new_input[n] = input_seed[n]
            #只有三种情况，所以大于长度的情况就是input_left +1的情况，最后一个元素就是新增的
            size = len(input_seed[0])
            for j in (range(len(new_input)-len(input_seed))):
                new_input[-(j+1)] =  secrets.token_bytes(size)   #新增的input随机生成一个数据填补
        else:
            new_input = list(input_seed[:len(new_input)])
        # left_num = random.randint(0, len(new_input)-1)
        mean = random.randint(0,size*8)
        ##修改：
        for i in range(len(new_input)):
            new_input[i] = mutate_singleInput(new_input[i], mean, self.std_dev)
        return new_input

    
    def mutate(self, idx, input_seed):
        if 0 <= idx < self.methodNum:
            mutatorFunc = self.funcMap[idx]
            return mutatorFunc(input_seed)
