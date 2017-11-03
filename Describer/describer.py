#!/usr/bin/env python

class Describer1():
	'''
	Describer without dict
	'''
	def __init__(self,score):
		self.score = score
	def __get__(self,instance,owner):
		return self.score
	def __set__(self,instance,value):
		if value < 0 or value > 100:
			raise Exception('Value out of range[0-100],value:%s'%(value))
		self.score = value

class Describer2():
	'''
	Describer with normal dict
	'''
	instances = {}
	def __init__(self,score):
		self.score = score
	def __get__(self,instance,owner):
		return Describer2.instances[instance] 
	def __set__(self,instance,value):
		if value < 0 or value > 100:
			raise Exception('Value out of range[0-100],value:%s'%(value))
		Describer2.instances[instance] = value

import weakref
class Describer3():
	'''
	Describer with WeakKeyDictionary
	'''
	instances = weakref.WeakKeyDictionary()
	def __init__(self,score):
		self.score = score
	def __get__(self,instance,owner):
		return Describer3.instances[instance]
	def __set__(self,instance,value):
		if value < 0 or value > 100:
			raise Exception('Value out of range[0-100],value:%s'%(value))
		Describer3.instances[instance] = value


class Test():
	score1 = Describer1(0)
	score2 = Describer2(0)
	score3 = Describer2(0)
	def __init__(self,score1,score2,score3):
		self.score1 = score1
		self.score2 = score2
		self.score3 = score3

t = Test(0,0,0)
x = Test(0,0,0)

t.score1
x.score1
t.score1 = 3
t.score1
x.score1

t.score2
x.score2
t.score2 = 33
t.score2
x.score2

t.score3
x.score3
t.score3 = 99
t.score3
x.score3

'''
----------------------------------------------------------------
|Describer1:         |Describer2:         |Describer3:         |
|>>> t.score1        |>>> t.score2        |>>> t.score3        |
|0                   |0                   |0                   |
|>>> x.score1        |>>> x.score2        |>>> x.score3        |
|0                   |0                   |0                   |
|>>>                 |>>>                 |>>>                 |
|>>> t.score1 = 3    |>>> t.score2 = 33   |>>> t.score3 = 99   |
|>>> t.score1        |>>> t.score2        |>>> t.score3        |
|3                   |33                  |99                  |
|>>> x.score1        |>>> x.score2        |>>> x.score3        |
|3                   |0                   |0                   |
----------------------------------------------------------------
Desription1(下称D1,D2/D3同理)是一个描述符，但是它有一个最大的问题：在Test类中，由于score(n)是类属性，对于这个类的各个实例来说，类属性是公共的，这样的话，只要实例A改变了该属性的值，其余的B，C，D等等其他实例的该属性也都改变了，这显然是不能接受的。
于是D2解决了这个问题，D2在描述符中持有一个字典instances，该字典的"K:V"为"实例:属性值",类似 {实例1:属性值1, 实例2:属性值2, 实例3:属性3 ......},这样，每次赋值时，通过__set__方法将"实例n:属性值n"存入该字典，取值时再通过__get__方法将指定对象(Key)的值通过字典取出该指定实例对应的属性值，不同实例的同名属性值不再相互干扰。
而D3则更进一步，利用(键)弱引用字典，当描述符外部不再使用某个实例时，描述符中的字典也不再维护该实例(即不再维护该键)，这样就进一步优化了程序，毕竟内部一直持有该"实例:属性值"就是为了外部服务的，如果外部都不用了，内部也就不必再耗费资源多占用这个键值对了。

弱引用：Python的垃圾回收机制会回收 引用数为0 或 只有弱引用 的对象。如下例
---------------------
import weakref
class T():
	pass

a = T()
b = weakref.ref(a)

del a
---------------------
其中当a被删除后，作为弱引用的b对应的对象T()由于没有其他非弱引用，也将被回收。
'''
