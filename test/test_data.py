import pickle
import random
import os
import time


num = 10 # common groups start from key=11

def randomColor():
    chars = ['1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
    colors =  [chars[random.randint(0,14)] for i in range(6)]
    return "#" + ''.join(colors)

def fun_groups(res, level=4):
	if level==0:
		return
	global num	
	for i in range(level):
		num += 1
		x = ["groups_{0}".format(num), num, []]
		res.append(x)
		fun_groups(x[2], level-1)

def fun_tags(num):
	return [[i, "Tag_{0}".format(i), randomColor()] for i in range(num)] # tag=0 => default tag


def fun_items(max_item, max_group, max_tag):
	scriptPath = os.path.abspath(__file__)
	c_time = time.strftime("%Y-%m-%d",time.localtime(time.time()))
	return [[
		"name_bla_bla_{0}".format(i), 
		random.randint(1,max_group), 
		list(set([random.randint(1,max_tag) for i in range(random.randint(1,max_tag))])), 
		scriptPath, 
		c_time, 
		"blablabla" if random.randint(1,10)>5 else ""] for i in range(1, max_item+1)]




if __name__ == "__main__":

	group_level, num_tag, num_item = 4, 10, 5000

	groups=[['Ungrouped', 1, []], ['Unreferenced', 2, []], ['All Groups', 3, []]] # default groups
	fun_groups(groups, group_level)
	
	data = {
		"Tagit": "0.5", 
		"groups": ["Group", "key", groups],
		"tags": fun_tags(num_tag),
		"items": fun_items(num_item, num, num_tag)
	}

	with open('test.dat', 'wb') as f:
		pickle.dump(data, f)