import pickle, os, sys, inspect, thread, time, math, datetime
from sklearn import svm
import numpy as np
from sklearn.multiclass import OneVsOneClassifier
from time import sleep
src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = '../lib/x64' if sys.maxsize > 2**32 else '../lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))
import Leap
from Leap import Bone
VALID=0
LEFT_HAND=0
RIGHT_HAND=11
BONE_NUM=[3,4,4,4,4]
COLLECT_DATA=1
CHECK_DATA=2
IDLE=0
ready=1
class mlistener(Leap.Listener):
    curret_count=0
    collect_count=1
    frame_buf=list()
    buf=list()
    meaning=""
    filling=IDLE
    def process_data(self):
        for frame in self.frame_buf:
            hands=frame.hands
            data=[0]*11
            data[0]=[0]*12
            for hand in hands:
                if hand.is_left and hand.is_valid:
                    left=hand
                    data[VALID][LEFT_HAND]=1
                if hand.is_right and hand.is_valid:
                    right=hand
                    data[VALID][RIGHT_HAND]=1
            if data[VALID][LEFT_HAND]:
                #计算左手需要的量，并填入data对应位置
                for i in range(1,6):
                    fingers=left.fingers
                    finger=0
                    for fg in fingers:
                        if fg.type==i-1:
                            finger=fg
                    if finger and finger.is_valid:
                        data[VALID][0+i]=1
                        old=(0,0,0)
                        new=(1,1,1)
                        n=BONE_NUM[i-1]
                        data[i]=[0]*n
                        #data[i]是手指i的数据，[angle1,angle2,angle3,direction]
                        for j in range(4-n,3):
                            if finger.bone(j).is_valid and finger.bone(j+1).is_valid:
                                old=finger.bone(j).next_joint-finger.bone(j).prev_joint
                                new=finger.bone(j+1).next_joint-finger.bone(j+1).prev_joint
                                if new.magnitude * old.magnitude==0:
                                    print i,j,new,old
                                cos=old.dot(new)/old.magnitude/new.magnitude
                                if cos > 1:
                                    cos=1
                                if cos < -1:
                                    cos=-1
                                #这里存下关节的余弦值，换成角度
                                data[i][j-4+n]=math.acos(cos) * 180 / math.pi
                        direction=finger.bone(1).next_joint-finger.bone(1).prev_joint
                        #将direction 用两个角度alpha beta存储
                        alpha=direction.yaw * 180 / math.pi
                        beta=direction.roll * 180 / math.pi
                        data[i][n-1]=[alpha,beta]
                    else:
                        print 'finger invalid'
            if data[VALID][RIGHT_HAND]:
                #计算右手
                for i in range(1,6):
                    fingers=right.fingers
                    finger=0
                    for fg in fingers:
                        if fg.type==i-1:
                            finger=fg
                    if finger and finger.is_valid:
                        data[VALID][5+i]=1
                        old=(0,0,0)
                        new=(1,1,1)
                        n=BONE_NUM[i-1]
                        data[5+i]=[0]*n
                        #data[i],手指i的数据,是一个list=[angle1,angle2,angle3,direction]
                        for j in range(4-n,3):
                            if finger.bone(j).is_valid and finger.bone(j+1).is_valid:
                                old=finger.bone(j).next_joint-finger.bone(j).prev_joint
                                new=finger.bone(j+1).next_joint-finger.bone(j+1).prev_joint
                                cos=old.dot(new)/old.magnitude/new.magnitude
                                if cos > 1:
                                    cos=1
                                if cos < -1:
                                    cos=-1
                                #这里存下关节的余弦值，是否应该换成角度？
                                data[5+i][j-4+n]=math.acos(cos) * 180 / math.pi
                        direction=finger.bone(1).next_joint-finger.bone(1).prev_joint
                        #将direction 用两个角度alpha beta存储
                        alpha=direction.yaw * 180 / math.pi
                        beta=direction.roll * 180 / math.pi
                        data[5+i][n-1]=[alpha,beta]
                        
            if self.filling==COLLECT_DATA:
                self.buf.append([data,self.meaning])
            if self.filling==CHECK_DATA:
                self.buf.append(data)
        return self.buf
    def on_connect(self, controller):
        print "connected"
    def on_frame(self, controller):
        global ready
        if ready:
            return
        if self.current_count>=self.collect_count:
            ready=1
            return
        frame=controller.frame()
        self.frame_buf.append(frame)
        self.current_count+=1
    def set_collect(self, num, meaning):
        global ready
        self.current_count=0
        self.buf=list()
        self.meaning=meaning
        self.collect_count=num
        self.filling=COLLECT_DATA
        self.frame_buf=list()
        ready=0
    def set_check(self, maxcount):
        global ready
        self.buf=list()
        self.current_count=0
        self.collect_count=maxcount
        self.filling=CHECK_DATA
        self.frame_buf=list()
        ready=0
class collect_data:
    def __init__(self):
        self.listener=mlistener()
        controller = Leap.Controller()
        controller.add_listener(self.listener)
        self.start_record()
    #输入记录帧数，手语语义，按下enter开始记录，把信息保存到文件中
    def start_record(self):
        global ready
        meaning = raw_input("input meaning")
        num = input("num")
        print "enter"
        sys.stdin.read(1)
        print "start..."
        self.listener.set_collect(num,meaning)
        begin=datetime.datetime.now()
        while 1:
            if ready:
                break
            sleep(1)
        end=datetime.datetime.now()
        print end-begin
        result=self.listener.process_data()
        func = lambda x: [y for l in x for y in func(l)] if type(x) is list else [x]
        result=func(result)#展开
        f=open(meaning,'w')
        pickle.dump(result,f)
        f.close()
class check_gesture:
    def __init__(self, datafile):
        self.listener=mlistener()
        f=open(datafile,'r')
        self.datalist=pickle.load(f)
        f.close()
    def start_check(self):
        num = 300#input("输入记录帧数")
        print "按下enter开始记录"
        sys.stdin.read(1)
        print "开始记录..."
        self.listener.set_check(num)
        
def merge_record(self,dst,src):
    #dst=dst+src 合并src到dst中
    f=open(dst,'r')
    list1=pickle.load(f)
    f.close()
    f=open(src,'r')
    list2=pickle.load(f)
    f.close()
    list1.extend(list2)
    f=open(dst,'w')
    pickle.dump(list1,f)
    f.close()
def read_data(filename):
    f=open(filename,'r')
    obj=pickle.load(f)
    f.close()
    return obj
def remove_label(filename,label):
    l=read_data(filename)
    out=list()
    for it in l:
        if it[1] != label:
            out.append(it)
    f=open(filename,'w')
    pickle.dump(out,f)
    f.close()
def analyze(filename):
    x_data=list()
    y_label=list()
    data=read_data(filename)
    for data_item in data:
        x_data.append([data_item[0:-1]])
        y_label.append(data_item[-1])
    CLF=OneVsOneClassifier(svm.SVC(gamma=0.0001,C=50,probability=True,random_state=0)).fit(x_data,y_label)
    print CLF.score(x,y)
if __name__ == '__main__':
    collecter = collect_data()
