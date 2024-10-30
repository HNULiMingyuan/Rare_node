import os
import secrets
import random

class Analysis:
    '''
    根据测试覆盖率结果分析覆盖率情况，筛选种集，种集权重赋值
    '''

    def __init__(self) -> None:
        pass

    #计算总的覆盖率   
    #覆盖率表示格式为二进制表示格式，以GCD 为例子：1011等类似的表示格式
    def Total_Coverage(self, total_coverage,current_coverage):
        Total_coverage = total_coverage | current_coverage
        return Total_coverage

#判断当前input产生的覆盖率是否有增加，如果增加返回True，没有增加返回False
    def Judge_coverage(self, current_coverage, total_coverage):
        # reverse_total = (2**(Real_CoverageSize+1)-1) ^ total_coverage
        if (current_coverage & ~total_coverage):
            flag = True
        else:
            flag = False
        return flag

#判断测试输入的有效性
    def judge_InputData(self, input_data):
        result = 1
        return result

#给定总覆盖信息，计算覆盖率
    def get_coverage_rate(self, totalcoverage):
        sum = 0
        for i in totalcoverage:
            sum += int(i)
        coveragerate = sum/len(totalcoverage)
        return coveragerate
    
    def result_analyse(self):
        outfilename = "node_flipping.txt"
        with open(outfilename,'r') as f:
            lines = f.readlines()
        coveragemessage = lines[-1].split()[-1]
        return coveragemessage
    
    def Total_Coverage(self, oldcoverage, currentcoverage):
        totalcoverage =  ''.join(random.choice('0') for _ in range(len(currentcoverage)))
        for i in range(len(totalcoverage)):
            if int(oldcoverage[i]) == 0:
                if int(currentcoverage[i]) == 1:
                    list_data = list(totalcoverage)
                    list_data[i] = '1'
                    totalcoverage =  ''.join(list_data)
                else:
                    list_data = list(totalcoverage)
                    list_data[i] = '0'
                    totalcoverage =  ''.join(list_data)
            else:
                list_data = list(totalcoverage)
                list_data[i] = '1'
                totalcoverage =  ''.join(list_data)
        return totalcoverage
    

    def write_Coverage(self, execution_time, coverage_rate, data_file_name):
        with open(data_file_name, 'a') as f:
            f.write(str(execution_time) + "\t" + str(coverage_rate) + '\n')
