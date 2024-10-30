from mutate import *
from RunProcess import *
from Analysis import *
import time
import os

#读取rare_nodes信息
def read_RN(filename):
    rare_nodes = {}
    with open(filename, 'r') as f:
        lines = f.readlines()
    for line in lines:
        rare_nodes[line.split(':')[0]] = 0
    return rare_nodes

#读取rare_values的值
def read_RV(filename):
    rare_values = {}
    with open(filename,'r') as f:
        lines = f.readlines()
    for line in lines:
        rare_values[line.split(':')[0]] = int(line.split(':')[1])
    return rare_values

#计算当前测试被触发的trigger的覆盖率
def get_Current_trigger_coverage():
    trigger_coverage = 0
    return trigger_coverage

#获取总Trigger覆盖率
def get_Total_trigger_coverage(Current_coverage, Total_coverage):
    Total_coverage += Current_coverage
    return Total_coverage 


def main():
    files_to_clear = ['out.txt', 'node_flipping.txt', 'flip_count.txt']
    # 清空文件：如果文件存在，则清空内容
    for file in files_to_clear:
        with open(file, 'w') as f:
            pass   
    InputSize = 60   #测试电路的输入位宽————————需要根据检测电路修改
    maxExecution_time = 300000  #最大执行时间
    max_i = 100000#最大迭代次数
    iteration = 0   #迭代轮数
    coverage_rate = 0  #覆盖率
    totalcoverage = '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    state_itr = 0
    state_steps = 0

    #实例化类           
    genInput = Gen()
    process = Run()
    analysis = Analysis()

    #低活性节点相关信息初始化
    activatefile = "activity.txt"
    rare_nodes = read_RN(activatefile)
    rare_values = read_RV(activatefile)
    outputfile = "c880.saif" 

    #开始模糊测试
    #step1：产生初始输入
    seedset = genInput.getInitial_Seedset(InputSize)

    #记录运行覆盖率数据
    execution_time = 0
    data_file_name = "Result.out" #保存覆盖率结果
    os.system('rm ' + data_file_name)   #删除原有实验数据
    analysis.write_Coverage(execution_time, coverage_rate, data_file_name)
    #进入模糊测试循环执行模糊测试
    time_begin = time.time()
    Total_trigger_coverage = 0 
    while(execution_time < maxExecution_time and Total_trigger_coverage < 1):
        coverage_rate = analysis.get_coverage_rate(totalcoverage)
        old_coverage = totalcoverage
        iteration += 1
        print("Seedset before getting input seed:", seedset)
        print("Type of seedset:", type(seedset))
        input_seed = genInput.get_input_seed(seedset)
        action = 1
        new_input = genInput.mutate(action,input_seed)
        #intermediate_state = genInput.getIntermediate_states(InputSize)
		
		#同一个状态如果超过1000steps覆盖率没有提升则更换状态
        # test_input = []
        # for i in new_input:
        #     test_input.append(i)
        # test_input.insert(0,intermediate_state[state_itr])
        # print("test_input: ")
        # print(test_input)
        # print("结束打印")
        print("mutated_seed: ")
        print(input_seed)
        print("结束打印")
        print("Seedset:")
        for k,v in seedset.items():
            print(str(k)+' : '+str(v))
#————————————————————————————————————————————————————————
		#2、执行初始测试向量
        process.runProcess(new_input)
#————————————————————————————————————————————————————————
		#3、分析运行结果，筛选种集以及对种集进行权重赋值
        coverage_message = analysis.result_analyse()  # 获得覆盖率信息
        new_seedset, new_rare_nodes = genInput.update_seedset(
            input_seed, new_input, seedset, coverage_message, totalcoverage, 
            rare_nodes, rare_values, outputfile) 
        seedset = new_seedset
        rare_nodes = new_rare_nodes
        totalcoverage = analysis.Total_Coverage(old_coverage, coverage_message)
        
        #判断是否一个中间状态已经超过1000次未增加新的覆盖率，如果一直未增加覆盖率，则更换中间状态
        #继续搜索
    #     if totalcoverage == old_coverage:
    #         state_steps += 1
	# #如果覆盖率没有增长则state_steps加1，如果超过1000步没有增长则认为此状态附近的节点已经被基本探索完，更换其他状态继续探索，同时state_steps重置为0
    #     if state_steps == 1000:
    #         state_itr += 1
    #         state_itr = state_itr%len(intermediate_state)
    #         state_steps = 0
                  
        #print("TotalCoverage:——————————————")
        #print(bin(totalcoverage)[2:])
        #print("结束打印TotalCoverage————————————————")
        #print("循环轮数：", iteration)
		#结束时间
        print("TotalCoverage:——————————————")
        print(totalcoverage)
        print("总覆盖率为：", coverage_rate)
        print("循环轮数：", iteration)
        time_end = time.time()
        #程序执行时间
        execution_time = time_end - time_begin
		# write_Coverage(iteration, totalcoverage,Real_CoverageSize ,valid_CoverageSize, data_file_name )
        if totalcoverage != old_coverage:
            print("coverage_rate:",coverage_rate)
            analysis.write_Coverage(execution_time, coverage_rate, data_file_name)
        
        time_end = time.time()
        execution_time = time_end - time_begin
        rate = process.runProcess(new_input)
        # Current_trigger_coverage = get_Current_trigger_coverage()
        # Total_trigger_coverage = get_Total_trigger_coverage(Current_trigger_coverage, Total_trigger_coverage)

        if rate == 1.0:
            print("Rate reached 1.0, stopping test.")
            break


if __name__ == "__main__":
    main()
