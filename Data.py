import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import tkinter as tk
from tkinter import filedialog
import xml.dom.minidom
import os
import re
import threading
import copy
import json
import time
import pandas as pd
import xml.etree.ElementTree as ET


class test(QWidget):

    def __init__(self):
        super(test, self).__init__()

    def setupUi(self, path):
        self.setFixedSize(400, 63)
        self.main_widget = QtWidgets.QWidget(self)
        self.label = QtWidgets.QLabel(self.main_widget)
        self.setWindowTitle('解析中...')
        self.label.setText("               ")
        self.label.move(10, 44)
        self.progressBar = QtWidgets.QProgressBar(self.main_widget)
        self.progressBar.setGeometry(QtCore.QRect(10, 10, 380, 30))
        self.flag = 0

        self.thread_2 = threading.Thread(target=self.toclose)
        self.thread_2.start()

        # 创建并启用子线程
        try:
            self.thread_1 = Data(path)
            self.thread_1.progressBarValue.connect(self.copy_file)
            self.thread_1.start()
            time.sleep(0.1)
            self.thread_1.join()
        except Exception as e:
            self.label.setText("解析失败")
            self.flag = 1

        self.thread_3 = threading.Thread(target=self.x)
        self.thread_3.start()

    def x(self):
        while not self.thread_1.isFinished() or not self.thread_2.is_alive():
            time.sleep(1)
            continue
        else:
            if self.label.text() == '解析成功':
                return
            else:
                self.label.setText("解析失败")
                time.sleep(1)
                self.close()

    def copy_file(self, i):
        self.progressBar.setValue(i)
        if i == 100:
            time.sleep(0.25)
            self.label.setText("解析成功")
            self.flag = 1

    def toclose(self):
        while self.flag != 1:
            time.sleep(0.5)
            continue
        else:
            time.sleep(1)
            self.close()

class Data(QThread):
    progressBarValue = pyqtSignal(int)  # 更新进度条

    def __init__(self, path):
        self.path = path
        self.key = path.split("/")[-1].split(".")[0]
        self.xmlpath = ''
        super(Data, self).__init__()
        self.exc = None

    def join(self):
        if self.exc:
            msg = "Error: %s"(self.exc[1])
            new_exc = Exception(msg)
            raise new_exc.with_traceback(self.exc[2])

    # 处理数据
    def run(self):
        che = {}
        canId = []
        sender = []
        receiverID = []
        cycleTimeId = []

        signalList = []
        name = []
        cycleTime = []
        startBit = []
        length = []
        note = []
        receiver = []

        path = self.path

        with open(path, 'rb') as f:
            # cur_encoding = chardet.detect(f.read(10000))['encoding']
            # print(cur_encoding)
            values = f.read().decode('gbk', errors='replace')  # 所有数据

        # 处理canID,name,sender,startBit,length,receiver
        result = re.findall(r'(BO_\s\w*\s\w*:\s\w\s\w*)((?:.|\n)*?)(?=BO_)', values, re.M)

        for i in result:
            a = i[1].replace('"  ', '" ')
            canId.append(re.findall(r'(?<=BO_\s)\w*(?=\s)', str(i), re.I))
            name.append(re.findall(r'(?<=SG_\s)\w+(?=\s:)', str(i), re.M))
            sender.append(re.findall(r'(?<=:\s\w\s)\w*', str(i), re.M))
            startBit.append(re.findall(r'(?<=\s:\s)\d*(?=\\|)', str(i), re.M))
            length.append(re.findall(r"(?<=\d\|)\d*(?=@)", str(i), re.M))
            receiver.append(re.findall(r'(?<=" )[\w,]*', a, re.S))

        # 处理ID的receiver,cycleTime
        # cycleTimeId.append(
        #     re.findall(r'(?<=BA_ "GenMsgCycleTime" BO_ ' + canId[i][0] + '\s)\d+(?=;)', values, re.M))
        try:
            for i in range(len(result)):
                c = re.findall(r'(?<=BA_ "GenMsgCycleTime" BO_ ' + canId[i][0] + '\s)\d+(?=;)', values, re.M)
                if c != []:
                    cycleTimeId.append(c)
                else: cycleTimeId.append(['0'])

                b = []
                if receiver[i] != []:
                    for j in range(len(name[i])):
                        a = receiver[i][j].split(',')
                        for k in range(len(a)):
                            b.append(a[k])
                    receiverID.append(list(set(b)))
                else:
                    a = []
                    receiverID.append(a)

            cycleTimeId[0] = [0]
        except Exception as e:
            self.exc = sys.exc_info()
            time.sleep(3.5)
            return

        # 处理cycleTime,note
        for i in range(len(result)):
            a = []
            b = []
            for j in range(len(name[i])):
                a1 = (re.findall(r'(?<=BA_ "GenSigCycleTime" SG_ ' + canId[i][0] + '\s' + name[i][j] + '\s)\d*(?=;)',
                                 values, re.I))
                b1 = (re.findall(r'(?<=CM_ SG_ ' + canId[i][0] + '\s' + name[i][j] + ')(\s+"(?:.|\n)*?")(?=;)', values,
                                 re.M))
                if not a1:
                    a1 = ['0']
                if not b1:
                    b1 = ['None']
                a.append(a1[0])
                b.append(b1[0].replace('\r\n', '').replace('"', '').replace(' ', ''))

            cycleTime.append(a)
            note.append(b)

            k = ((i + 1) / len(result)) * 100 * 0.95
            if k >= 95:
                time.sleep(1)
                break
            self.progressBarValue.emit(k)
            # print(k)
            # print('loading...%.2f' % k, "%")

        # 检查
        # for i in range(len(result)):
        # print(canId[i],len(name[i]),len(cycleTimeId[i]),len(startBit[i]),len(length[i]),len(note[i]),len(receiver[i]))
        # print(cycleTime[i],note[i])
        # print(canId[i][0])
        # print(cycleTimeId)
        # exit(0)

        # signalList字典
        try:
            for i in range(len(result)):
                lis = []
                for j in range(len(name[i])):
                    dic2 = {}
                    dic2_copy = copy.deepcopy(dic2)
                    dic2_copy["name"] = name[i][j]
                    dic2_copy["cycleTime"] = int(cycleTime[i][j])
                    dic2_copy["startBit"] = int(startBit[i][j])
                    dic2_copy["length"] = int(length[i][j])
                    dic2_copy["note"] = note[i][j]
                    dic2_copy["receiver"] = receiver[i][j]
                    lis.append(dic2_copy)
                    dic2.clear()
                signalList.append(lis)

            # 外层字典
            for i in range(len(result)):
                dic = {}
                dic_copy = copy.deepcopy(dic)
                dic_copy["canId"] = int(canId[i][0])
                dic_copy["sender"] = sender[i][0]
                dic_copy["reciver"] = receiverID[i]
                dic_copy["signalList"] = signalList[i]
                dic_copy["cycleTime"] = int(cycleTimeId[i][0])
                if int(canId[i][0]) < 10000:
                    che[int(canId[i][0])] = dic_copy
                dic.clear()
        except Exception as e:
            self.exc = sys.exc_info()
            # print(e)
            # print(self.exc)
            time.sleep(3.5)
            return

            # 保存到json
        with open('.\\' + self.key + '.json', 'w', encoding='utf-8') as fp:
            json.dump(che, fp)
        k = 100
        self.progressBarValue.emit(k)

    # 生成表格数据
    def json_to_table(self, can, time, sample):
        table = pd.read_json('.\\' + self.key + '.json', encoding='utf-8')
        timeout = time * table.loc["cycleTime"][can]
        sampleCycle = sample * table.loc["cycleTime"][can]

        rolingcounterStartBit = 0
        rolingcounterLenth = 0
        crcStartBit = 0
        crcLenth = 0
        priority = 3

        for i in range(len(table.loc["signalList"][can])):
            if r'Rolling' in table.loc["signalList"][can][i]["name"]:
                index = i
                rolingcounterStartBit = table.loc["signalList"][can][index]["startBit"]
                rolingcounterLenth = table.loc["signalList"][can][index]["length"]

        for j in range(len(table.loc["signalList"][can])):
            if r'Check' in table.loc["signalList"][can][j]["name"]:
                index = j
                crcStartBit = table.loc["signalList"][can][index]["startBit"]
                crcLenth = table.loc["signalList"][can][index]["length"]
        data_row = [can, timeout, sampleCycle, rolingcounterStartBit, rolingcounterLenth, crcStartBit, crcLenth,
                    priority]
        return data_row

    # xml模板
    def xml_example(self, df):

        whitelists = list(df["canId"])
        timeouts = list(df["timeout"])
        sampleCycles = list(df["sampleCycle"])
        rollingcounterStartBits = list(df["rollingcounterStartBit"])
        rollingcounterLenths = list(df["rollingcounterLenth"])
        crcStartBits = list(df["crcStartBit"])
        crcLenths = list(df["crcLenth"])
        prioritys = list(df["priority"])
        t = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))

        doc = xml.dom.minidom.Document()
        rootnode = doc.createElement('root')
        data = doc.createElement('data')
        respStatus = doc.createElement('respStatus')
        respStatus.appendChild(doc.createTextNode('OK'))
        errorCode = doc.createElement('errorCode')
        errorCode.appendChild(doc.createTextNode(''))
        errorMsg = doc.createElement('errorMsg')
        errorMsg.appendChild(doc.createTextNode(''))
        confTimestamp = doc.createElement('confTimestamp')
        confTimestamp.appendChild(doc.createTextNode(str(t)))
        moduleSwitch = doc.createElement('moduleSwitch')
        moduleSwitch.appendChild(doc.createTextNode('true'))

        doc.appendChild(rootnode)
        rootnode.appendChild(respStatus)
        rootnode.appendChild(errorCode)
        rootnode.appendChild(errorMsg)
        rootnode.appendChild(confTimestamp)
        rootnode.appendChild(moduleSwitch)
        rootnode.appendChild(data)

        for i in range(len(whitelists)):
            canIdWhiteList = doc.createElement('canIdWhiteList')
            canId = doc.createElement('canId')
            canId.appendChild(doc.createTextNode(str(whitelists[i])))
            timeout = doc.createElement('timeout')
            timeout.appendChild(doc.createTextNode(str(timeouts[i])))
            sampleCycle = doc.createElement('sampleCycle')
            sampleCycle.appendChild(doc.createTextNode(str(sampleCycles[i])))
            rollingcounterStartBit = doc.createElement('rollingcounterStartBit')
            rollingcounterStartBit.appendChild(doc.createTextNode(str(rollingcounterStartBits[i])))
            rollingcounterLenth = doc.createElement('rollingcounterLenth')
            rollingcounterLenth.appendChild(doc.createTextNode(str(rollingcounterLenths[i])))
            crcStartBit = doc.createElement('crcStartBit')
            crcStartBit.appendChild(doc.createTextNode(str(crcStartBits[i])))
            crcLenth = doc.createElement('crcLenth')
            crcLenth.appendChild(doc.createTextNode(str(crcLenths[i])))
            priority = doc.createElement('priority')
            priority.appendChild(doc.createTextNode(str(prioritys[i])))

            canIdWhiteList.appendChild(canId)
            canIdWhiteList.appendChild(timeout)
            canIdWhiteList.appendChild(sampleCycle)
            canIdWhiteList.appendChild(rollingcounterStartBit)
            canIdWhiteList.appendChild(rollingcounterLenth)
            canIdWhiteList.appendChild(crcStartBit)
            canIdWhiteList.appendChild(crcLenth)
            canIdWhiteList.appendChild(priority)

            data.appendChild(canIdWhiteList)

        try:
            root = tk.Tk()
            root.withdraw()
            path = filedialog.asksaveasfilename(defaultextension='.xml', initialdir='C:\\', initialfile=self.key + '.xml',
                                                parent=root, title='xml模板另存为')
            # if path:
            with open(path, 'w') as fp:
                if not os.path.exists(path):
                    os.mkdirs(path)
                doc.writexml(fp, indent='\t', addindent='\t', newl='\n', encoding="utf-8")
            self.xmlpath = path
        except Exception as e:
            # print(e)
            return
        return self.xmlpath

    def search_by_id(self, id):
        table = pd.read_json('.\\' + self.key + '.json', encoding='utf-8')
        data = []
        ban_name = ['crc', 'Rolling', 'Check']
        for i in range(len(table.loc['signalList'][id])):
            if all(ba not in table.loc["signalList"][id][i]["name"] for ba in ban_name):
                name = table.loc["signalList"][id][i]["name"]
                note = table.loc["signalList"][id][i]["note"]
                row = [id, name, note]
                data.append(row)
        return data

    def search_by_word(self, word):
        table = pd.read_json('.\\' + self.key + '.json', encoding='utf-8')
        data = []
        ban_name = ['crc', 'Rolling', 'Check']
        for i in range(len(table.iloc[0])):
            for j in table.iloc[3].values[i]:
                if word in j['name']:
                    if all(ba not in j['name'] for ba in ban_name):
                        name = j['name']
                        note = j['note']
                        id = table.iloc[3].index[i]
                        row = [id, name, note]
                        data.append(row)
        return data

    # 上传规则
    def uploadrulelist(self, ulp=1000, ulCN=60, sd=8, md=3, py=3, zg='true', **kwargs):

        uploadRuleList = ET.Element("uploadRuleList")
        # uploadRuleList = ET.SubElement(data, 'uploadRuleList')
        collectionCondition = ET.SubElement(uploadRuleList, 'collectionCondition')

        for i in kwargs['dataframe'].values:
            collectionContent = ET.SubElement(uploadRuleList, 'collectionContent')
            collectionContent.text = i[1]
            canId = ET.SubElement(uploadRuleList, 'canId')
            canId.text = str(i[0])
            note = ET.SubElement(uploadRuleList, 'note')
            note.text = str(i[2])

        uploadCondition = ET.SubElement(uploadRuleList, 'uploadCondition')
        uploadPeriod = ET.SubElement(uploadCondition, 'uploadPeriod')
        uploadContentNumber = ET.SubElement(uploadCondition, 'uploadContentNumber')
        trigger = ET.SubElement(uploadCondition, 'trigger')
        event = ET.SubElement(trigger, 'event')
        afterEventHappen = ET.SubElement(trigger, 'afterEventHappen')
        uploadParameter = ET.SubElement(uploadRuleList, 'uploadParameter')
        sid = ET.SubElement(uploadParameter, 'sid')
        mid = ET.SubElement(uploadParameter, 'mid')
        priority = ET.SubElement(uploadParameter, 'priority')
        zipFlag = ET.SubElement(uploadParameter, 'zipFlag')

        if kwargs['flag'] == 0:
            collectionCondition.text = 'auto_collection'
        elif kwargs['flag'] == 1:
            collectionCondition.text = 'RUN_TIME%' + str(kwargs['RUN_TIME']) + '==0'
        else:
            collectionCondition.text = 'none'

        uploadPeriod.text = str(ulp)
        uploadContentNumber.text = str(ulCN)
        sid.text = str(sd)
        mid.text = str(md)
        priority.text = str(py)
        zipFlag.text = zg
        return uploadRuleList

    def uploadrulelist_change(self, tree):

        uploadCondition = tree.find('uploadCondition')
        trigger = uploadCondition.find('trigger')
        uploadParameter = tree.find('uploadParameter')
        collectionCondition_text = tree[0].text

        collectionContent_text = []
        canId = []
        note = []
        for element in tree.findall('collectionContent'):
            collectionContent_text.append(element.text)
        for i in tree.findall('canId'):
            canId.append(i.text)
        for j in tree.findall('note'):
            note.append(j.text)

        uploadPeriod_text = uploadCondition[0].text
        uploadContentNumber_text = uploadCondition[1].text
        event_text = trigger[0].text
        afterEventHappen_text = trigger[1].text
        sid_text = uploadParameter[0].text
        mid_text = uploadParameter[1].text
        priority_text = uploadParameter[2].text
        zipFlag_text = uploadParameter[3].text

        dic = {'collectionCondition':collectionCondition_text,'collectionContent':collectionContent_text,'uploadPeriod':
            uploadPeriod_text,'uploadContentNumber':uploadContentNumber_text,'event':event_text,'afterEventHappen':
            afterEventHappen_text,'sid':sid_text,'mid':mid_text,'priority':priority_text,'zipFlag':zipFlag_text,
               'canId':canId,'note':note}
        # print(dic)
        return dic

    def sava_uploadrulelist(self, node, xmlpath):
        try:
            open(xmlpath)
        except Exception as e:
            print(e)
            return

        tree = ET.parse(xmlpath)
        root = tree.getroot()
        data = root.find('data')
        print(node.find('collectionCondition'))
        if node.find('collectionCondition') != None:
            for i in node.findall('canId'):
                node.remove(i)
            for j in node.findall('note'):
                node.remove(j)
        data.append(node)
        tree.write(xmlpath, encoding='utf-8')

    def deviceStorage(self, max, df3):
        deviceStorage = ET.Element("deviceStorage")
        maxStorageSize = ET.SubElement(deviceStorage, 'maxStorageSize')
        maxStorageSize.text = str(max)
        usedStorageScale_text = list(df3["usedStorageScale"])
        collectLevelGE_text = list(df3["collectLevelGE"])

        for i in range(len(usedStorageScale_text)):
            degradeCollectCondition = ET.SubElement(deviceStorage, 'degradeCollectCondition')
            usedStorageScale = ET.SubElement(degradeCollectCondition, 'usedStorageScale')
            usedStorageScale.text = str(usedStorageScale_text[i])
            collectLevelGE = ET.SubElement(degradeCollectCondition, 'collectLevelGE')
            collectLevelGE.text = str(collectLevelGE_text[i])
        return deviceStorage

# 文件选择
def choose_data():
    root = tk.Tk()
    root.withdraw()
    fpath = filedialog.askopenfilename()
    """设置按钮显示所有车型的dbc"""
    # for path in fpath:
    #     if not path.endswith('dbc'):
    #         print('文件有误')
    #         exit(0)
    #     else:
    return fpath


# path = choose_data()
if __name__ == '__main__':
    df = pd.DataFrame([[608, 120, 40, 0, 0, 0, 0, 3],
                       [614, 120, 40, 0, 0, 0, 0, 3],
                       [688, 150, 50, 0, 0, 19, 4, 3],
                       [760, 300, 100, 0, 0, 0, 0, 3]
                       ], columns=["canId", "timeout", "sampleCycle", "rollingcounterStartBit", "rollingcounterLenth",
                                   "crcStartBit", "crcLenth", "priority"])

    df2 = pd.DataFrame([[760, 'HU_DVRErrorRecord', 'aaaaaaaaaaaa'],
                        [760, 'HU_SDCapacity', 'aaaaaaaaaaaa'],
                        [760, 'HU_DVRSystemImprint', 'aaaaaaaaaaaa'],
                        [760, 'HU_RebroadcastReq', 'aaaaaaaaaaaa'],
                        [760, 'HU_RealTimeReq', 'aaaaaaaaaaaa'],
                    ], columns=["canId", "信号名", "注释"])

    df3 = pd.DataFrame([[0.2, 2],
                        [0.7, 3]
                        ], columns=['usedStorageScale', 'collectLevelGE'])

    # path = 'G:/xml/2InfoCAN_S111.dbc'
    path = choose_data()
    d = Data(path)
    # d.search_by_id(598)
    # d.search_by_word('BCM')
    # app = QtWidgets.QApplication(sys.argv)
    # testIns = test()
    # testIns.setupUi(path)
    # testIns.show()
    # sys.exit(app.exec_())

    # d.run()
    # a = d.json_to_table(946,3,1)
    # print(a)
    d.xml_example(df)
    # print(d.xmlpath)
    # d.xmlpath = r'C:/Users/201904622/Desktop/2InfoCAN_S111.xml'
    # rule1 = d.uploadrulelist(flag=0, dataframe=df2)
    # rule2 = d.uploadrulelist(flag=0, dataframe=df2, sd=10000000)

    # d.sava_uploadrulelist(rule1)
    # d.sava_uploadrulelist(rule2)
    # dic = d.uploadrulelist_change(rule1)

    # a = d.deviceStorage(63400, df3)
    # d.sava_uploadrulelist(a)
