import pickle
import random
import os
import time


num = 9 # common groups start from key=11

def randomColor():
    chars = ['1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
    colors =  [chars[random.randint(0,14)] for i in range(6)]
    return "#" + ''.join(colors)

def randomInt(lbound, ubound=None):
	if ubound==None:
		lbound, ubound = 1, lbound
	return random.randint(lbound, ubound)

def fun_groups(res, level):
	if level==0:
		return
	global num	
	for i in range(level):
		num += 1
		x = ["Groups_{0}".format(num), num, []]
		res.append(x)
		fun_groups(x[2], level-1)

def fun_tags(num):
	return [[i+1, "Tag_{0}".format(i+1), randomColor()] for i in range(num)]


def fun_items(max_item, max_group, max_tag):
	scriptPath = os.path.dirname(os.path.abspath(__file__))
	c_time = time.strftime("%Y-%m-%d",time.localtime(time.time()))
	return [[
		"name_{0}_{1}".format('bla'*randomInt(3), randomInt(max_item)), # make duplicated items
		randomInt(10,max_group), 
		list(set([randomInt(max_tag) for k in range(randomInt(max_tag))])), # random tags
		scriptPath if randomInt(10)>5 else 'it/is/aninvalid/path', # invalid path in some probability
		c_time, 
		'{0},{1}'.format("bla"*randomInt(5), "hia"*randomInt(0,5))] for i in range(max_item)]



if __name__ == "__main__":

	group_level, num_tag, num_item = 3, 10, 1000

	groups=[['All Groups', 1, [
            ['Ungrouped', 2, []],
            ['Unreferenced', 3, []],
            ['Duplicated', 4, []],
            ['Trash', 5, []]
        ]]] # default groups
	fun_groups(groups, group_level)

	tags = [[0, 'NoTag', '#000000']] # default tag
	tags.extend(fun_tags(num_tag))	
	
	data = {
		"Tagit": "0.5", 
		"groups": ["Group", "key", groups],
		"tags": tags,
		"items": fun_items(num_item, num, num_tag)
	}

	with open('test.dat', 'wb') as f:
		pickle.dump(data, f)