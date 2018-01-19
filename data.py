import pickle, os, sys, inspect, thread, time, math, datetime
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
                                #这里存下关节的余弦值，是否应该换成角度？
                                data[i][j-4+n]=cos
                        direction=finger.bone(1).next_joint-finger.bone(1).prev_joint
                        data[i][n-1]=direction.normalized.to_tuple()
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
                                #这里存下关节的余弦值，是否应该换成角度？
                                data[5+i][j-4+n]=cos
                        direction=finger.bone(1).next_joint-finger.bone(1).prev_joint
                        data[5+i][n-1]=direction.normalized.to_tuple()
                        
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
        meaning = raw_input("输入手语语义")
        num = input("输入记录帧数")
        print "按下enter开始记录"
        sys.stdin.read(1)
        print "开始记录..."
        self.listener.set_collect(num,meaning)
        begin=datetime.datetime.now()
        while 1:
            if ready:
                break
            sleep(1)
        end=datetime.datetime.now()
        print end-begin
        result=self.listener.process_data()
        f=open(meaning,'w')
        pickle.dump(result,f)
        f.close()
    def merge_record(self,file1,file2):
        #把两个手语数据合并成名为data的数据文件
        f=open(file1,'r')
        list1=pickle.load(f)
        f.close()
        f=open(file2,'r')
        list2=pickle.load(f)
        f.close()
        l=[list1,list2]
        f=open('data','w')
        pickle.dump(l,f)
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
    def calculate_gesture(self, data):
        #Pi=eδ(EDi-ED1)ξk=ΣPi
def read_data(filename):
    f=open(filename,'r')
    obj=pickle.load(f)
    f.close()
    return obj
if __name__ == '__main__':
    collecter = collect_data()
