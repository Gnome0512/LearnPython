#!/usr/bin/env python

class LazyProperty():
    def __init__(self,func):
        self.func = func
    def __get__(self,instance,owner):
        value = self.func(instance)
        setattr(instance,self.func.__name__,value)
        return value

class Test():
    Pi = 3.14
    def __init__(self,r):
        self.r = r
    @LazyProperty
    def area(self):
        print('area calcu...')
        return self.Pi*self.r**2

t=Test(1)

a=t.area
b=t.area
c=t.area
print(a,b,c)


'''
OUTPUT
>>> t.area
area calcu...
3.14
>>> t.area
3.14
>>> t.area
3.14
'''



'''
---------------------------------------------------
装饰器(用类实现)说明:
---------------------------------------------------
  和用函数实现的装饰器类似，只不过这种装饰器返回的是一个被类 __init__ 修饰的实例，在上例中，运行t.area时，实际上是在运行 t.LazPproperty(area)
  事实上，如果直接使用 t.LazPproperty(area) 是会报错的，毕竟LazPproperty(area)这个实例是无法被调用的(没有实现__call__方法)，这里就相当于把Test类中的area函数转换成了area类属性，而area属性值就是上面的 LazPproperty(area)，这一点可以通过 Test.__dict__ 查看确认
  相当于：
LazyProperty类不变
class Test():
	Pi = 3.14
	def __init__(self,r):
		self.r = r  
	def area(self):
		print('area calcu...')
		return self.Pi*self.r**2
	area = LazyProperty(area)
(上面本来是想用"def area_t(self) ...... area = LazyProperty(area_t)"的，但是这样写了之后用t.arae发现print还是会打印,后来发现是本描述符在setattr时会把值绑定到函数名的【同名】变量上，即要调用t.area_t才行，所以又该回了函数名)
---------------------------------------------------
描述符说明:
---------------------------------------------------
  通过"实例.属性"得到值时，顺序如下:
    1,调用实例的 __getattribute__ 方法
    2,type(实例).__dict__('属性').__get__(实例,type(实例)) 查找数据描述符
    3,实例.__dict__('属性') 查找本实例中是否有此属性
    4,type(实例).__dict__('属性') 查找本类的类属性中是否有此属性
    5,type(实例).__dict__('属性').__get__(实例,type(实例)) 查找非数据描述符
    6,通过 __getattr__ 方法查找是否有此属性，没有则抛出异常
  上例中，t.area首先查看t是否有area属性，很明显，上面的装饰器部分已经讲过，area被转换为了类属性，实例是没有此属性的，所以按顺序到第二部找的时候发现有此类属性，故调用 type(t).__dict__('area')，即LazPproperty(area)得到其值,又因为解释器发现LazPproperty是一个描述符，则进一步调用 type(t).__dict__('area').__get__(self,t,type(t))方法
---------------------------------------------------
综上，类实现装饰器和描述符的运用构成了LazyProperty特性
---------------------------------------------------
'''
