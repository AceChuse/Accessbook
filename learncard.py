import os
import sys
import re
import pandas as pd
import random
import datetime
import time
import math

# 这里我们提供必要的引用。基本控件位于pyqt5.qtwidgets模块中。
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import QtGui

from LearnCardWidget import Ui_Form

_maxDate = datetime.datetime(datetime.MAXYEAR, month=12, day=31)
_minDate = datetime.datetime(datetime.MINYEAR, month=1, day=1)

with open("config.txt","r") as f:
    config = f.readlines()
    for co in config:
        if co[:11] == 'numNewCards': _numNewCards = int(re.sub(': *', ':', co).split(':')[1])
        elif co[:9] == 'cardfiles':
            _cardfiles = re.sub(': *', ':', co).split(':')[1]
            _cardfiles = re.sub(',', ' ', _cardfiles)
            _cardfiles = re.sub(' +', ' ', _cardfiles).split(' ')

# _numNewCards = 20
# _cardfiles = ['toeflJuxin.xlsx', 'words.xlsx']


_failDelta = datetime.timedelta(minutes = 3)
_onlyOneDelta = faildelta = datetime.timedelta(minutes = 10)


def argmin(*nums):
    amin, nmin = 0, nums[0]
    for i, num in enumerate(nums):
        if num < nmin: amin, nmin = i, num
    return amin

def ankiAlgorithm(quality, repetitions=0, easiness=2.5, interval=1):
    if quality < 0 and quality > 5: raise Exception('Over range!')

    # easiness = factor
    easiness = max(1.3, easiness + 0.1 - (5.0 - quality) * (0.08 + (5.0 - quality) * 0.02))

    # repetitions
    if quality < 3: repetitions = 0
    else: repetitions += 1

    # interval
    if repetitions <= 1: interval = 1
    elif repetitions == 2: interval = 6
    else: interval = round(interval * easiness)

    # next practice
    nextPracticeDate = datetime.datetime.now() + datetime.timedelta(days = interval)

    return {'rep': repetitions, 'ef': easiness, 'interval': interval, 'date': nextPracticeDate}


def levenshtein_distance(str1, str2):
    m, n = len(str1) + 1, len(str2) + 1

    # 初始化矩阵
    matrix = [[0] * n for i in range(m)]
    matrix[0][0] = 0

    for i in range(1, m):
        matrix[i][0] = matrix[i - 1][0] + 1
    for j in range(1, n):
        matrix[0][j] = matrix[0][j - 1] + 1

    for i in range(1, m):
        for j in range(1, n):
            if str1[i - 1] == str2[j - 1]:
                matrix[i][j] = min(matrix[i - 1][j - 1], matrix[i-1][j]+1, matrix[i][j-1]+1)
            else:
                matrix[i][j] = min(matrix[i - 1][j - 1]+1, matrix[i - 1][j]+1, matrix[i][j - 1]+1)

    return matrix[m - 1][n - 1]


class LearnNewCards(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.cards = {}
        for cardfile in _cardfiles:
            cards = pd.read_excel(cardfile, sheet_name=0).to_dict(orient='index')
            self.cards = dict(self.cards, **cards)
        print(self.cards)
        self.records = pd.read_excel('records.xlsx', sheet_name=0).to_dict(orient='index')
        self.init()
        self.initUI()

    def init(self):
        record_keys = self.records.keys()

        if os.path.exists('newCardKeys.xlsx'):
            self.keys = pd.read_excel('newCardKeys.xlsx', sheet_name=0).to_dict(orient='list')['key']
        else:
            self.keys = []

        if os.path.exists('newCardFailCards.xlsx'):
            self.failcards = pd.read_excel('newCardFailCards.xlsx', sheet_name=0
                                           ).to_dict(orient='records')
        else: self.failcards = []

        if os.path.exists('newCardOnlyOnes.xlsx'):
            self.onlyones = pd.read_excel('newCardOnlyOnes.xlsx', sheet_name=0
                                           ).to_dict(orient='records')
        else: self.onlyones = []

        if not (self.keys + self.failcards + self.onlyones):
            self.keys = [key for key in self.cards.keys() if key not in record_keys]
            self.keys = random.sample(self.keys, _numNewCards)

        # self.keys = ['toeflJuxin11', 'toeflJuxin12', 'toeflJuxin13', 'toeflJuxin14', 'toeflJuxin15',
        #              'toeflJuxin16', 'toeflJuxin17', 'toeflJuxin18', 'toeflJuxin19', 'toeflJuxin20',
        #              'toeflJuxin21', 'toeflJuxin22', 'toeflJuxin23', 'toeflJuxin24', 'toeflJuxin25',
        #              'toeflJuxin26', 'toeflJuxin27', 'toeflJuxin28', 'toeflJuxin29', 'toeflJuxin30'
        #              ]

        print('keys', self.keys)
        print('failcards', self.failcards)
        print('onlyones', self.onlyones)
        self.title = "Learn new cards."
        self.saveCurrent()

    def saveCurrent(self):
        #save current keys
        df = pd.DataFrame(self.keys, columns=['key'])
        df.to_excel('newCardKeys.xlsx')
        #save current failcards
        df = pd.DataFrame(self.failcards, columns=['key', 'time', 'ft', 'only', 'ascore'])
        writer = pd.ExcelWriter('newCardFailCards.xlsx')
        df.to_excel(writer, sheet_name='Sheet1')
        writer.sheets['Sheet1'].set_column('B:B', 15)
        writer.sheets['Sheet1'].set_column('C:C', 25)
        writer.sheets['Sheet1'].set_column('D:G', 8)
        # save current onlyones
        df = pd.DataFrame(self.onlyones, columns=['key', 'time', 'ft', 'only', 'ascore'])
        writer = pd.ExcelWriter('newCardOnlyOnes.xlsx')
        df.to_excel(writer, sheet_name='Sheet1')
        writer.sheets['Sheet1'].set_column('B:B', 15)
        writer.sheets['Sheet1'].set_column('C:C', 25)
        writer.sheets['Sheet1'].set_column('D:G', 8)

    def saveRecord(self):
        df = pd.DataFrame(list(self.records.values()), index = list(self.records.keys()),
                          columns=['rep', 'ef', 'interval', 'date'])
        writer = pd.ExcelWriter('records.xlsx')
        df.to_excel(writer, sheet_name='Sheet1')
        writer.sheets['Sheet1'].set_column('A:A', 15)
        writer.sheets['Sheet1'].set_column('B:B', 5)
        writer.sheets['Sheet1'].set_column('C:C', 11)
        writer.sheets['Sheet1'].set_column('D:D', 11)
        writer.sheets['Sheet1'].set_column('E:E', 25)

    def count(self):
        return len(self.keys) + len(self.failcards) + len(self.onlyones) + 1

    def initUI(self):
        self.setupUi(self)
        self.sentencelabels = [self.label_2, self.label_3, self.label_4]
        self.sentenceEdits = [self.textEdit, self.textEdit_2, self.textEdit_3]
        self.nextcard()

        self.pushButton.clicked.connect(self.incognizance)
        self.pushButton_2.clicked.connect(self.inputConfirm)
        self.pushButton_3.clicked.connect(self.nextcard)
        self.widget.close()
        self.setWindowTitle(self.title)
        self.show()

    def initOneCard(self, card):
        self.lineEdit.clear()
        self.lineEdit.setStyleSheet("background-color: white")
        self.textEdit.clear()
        self.textEdit.setStyleSheet("background-color: white")
        self.textEdit_2.clear()
        self.textEdit_2.setStyleSheet("background-color: white")
        self.textEdit_3.clear()
        self.textEdit_3.setStyleSheet("background-color: white")

        self.surplus.setText("还剩: " + str(self.count()) + "个")

        self.spell = card.get('spell')
        if self.spell is not None and str(self.spell) != 'nan':
            self.label.show()
            self.lineEdit.show()
            self.label.setText(card['解释'])
            self.spell = card['spell']
            self.lineEdit.setFocus()
        else:
            self.label.close()
            self.lineEdit.close()
            self.sentenceEdits[0].setFocus()

        self.sentences = []
        for i in range(1, 3):
            liju = (card.get('例句e' + str(i)), card.get('例句c' + str(i)))
            if liju[0] is None or str(liju[0]) == 'nan': break
            else: self.sentences.append(liju)
        self.len_sent = len(self.sentences)

        print('sentences', self.sentences)
        for i in range(self.len_sent):
            self.sentencelabels[i].setText(self.sentences[i][1])
            self.sentencelabels[i].show()
            self.sentenceEdits[i].show()
        for j in range(i+1, 3):
            self.sentencelabels[j].close()
            self.sentenceEdits[j].close()

        self.starttime = datetime.datetime.now()

    def inputConfirm(self, confirm=True):
        print('here1')
        self.costtime = (datetime.datetime.now() - self.starttime).seconds
        text = self.lineEdit.text().strip(' ')
        texts = [self.sentenceEdits[i].toPlainText().strip(' \n') for i in range(self.len_sent)]
        if not (text + ''.join(texts)) and confirm: return

        print('here2', self.spell)
        correct = True
        if_pass = False
        if self.spell is not None and str(self.spell) != 'nan':
            if self.spell == text: self.lineEdit.setStyleSheet("background-color: white; color:rgb(69, 138, 255);")
            else:
                correct = False
                self.lineEdit.setStyleSheet("background-color: white; color: red;")
            self.label.setText(self.label.text()+'\n'+self.spell)
            distance, alllen = levenshtein_distance(self.spell, text), len(self.spell)
        else:
            distance, alllen = 0, 0
        print('here3')

        if not ''.join(texts): correct = False

        if not (''.join(texts)):
            texts[0] = 'None'
            self.sentenceEdits[0].setPlainText(texts[0])
        for i in range(self.len_sent):
            _text = re.sub(' +', ' ', texts[i]).strip(' ').strip('\n')
            if _text:
                alllen += len(self.sentences[i][0])
                distance += levenshtein_distance(_text, self.sentences[i][0])
                if _text == self.sentences[i][0]: self.sentenceEdits[i].setStyleSheet("background-color: white; color:rgb(69, 138, 255);")
                else:
                    correct = False
                    self.sentenceEdits[i].setStyleSheet("background-color: white; color: red;")
            self.sentencelabels[i].setText(self.sentences[i][1] + '\n' + self.sentences[i][0])

        print('1 - distance / alllen = ', 1 - distance / alllen)
        score = (1 - distance / alllen) * 4
        if score == 4 and self.costtime < 1.36 * alllen: score = 5

        if alllen > 180 and score > 3.912 and score < 4: if_pass, score = True, score - 0.5

        self.dealResult(correct, score, if_pass)

    def label_5_setText(self, **kwargs):
        kwargs['time'] = kwargs['time'].strftime('%Y/%m/%d %H:%M:%S')
        self.label_5.setText(str(kwargs))

    def dealResult(self, correct, score, if_pass = False):
        if correct or if_pass:
            if self.nowstate == 'new':
                self.onlyones.append({'key': self.nowkey, 'time':  datetime.datetime.now() + _onlyOneDelta,
                                      'ft': 0, 'only': True, 'ascore': score})
                self.label_5_setText(**self.onlyones[-1], score=score)
            elif self.cardstate['only']:
                quality = (self.cardstate['ascore'] + score) / (
                        self.cardstate['ft'] + 2)
                record = self.records.get(self.nowkey)
                if record is None:
                    self.records[self.nowkey] = ankiAlgorithm(quality=quality)
                else:
                    self.records[self.nowkey] = ankiAlgorithm(
                        quality=quality, repetitions=record['rep'],
                        easiness=record['ef'], interval=record['interval'])
                self.label_5_setText(**self.records[self.nowkey], score=score)
            else:
                self.cardstate['only'] = True
                self.cardstate['ascore'] += score
                self.onlyones.append(
                    dict({'key': self.nowkey, 'time': datetime.datetime.now() + _onlyOneDelta}, **self.cardstate))
                self.label_5_setText(**self.onlyones[-1], score=score)
            self.widget.show()
            self.pushButton.close()

            self.saveRecord()
            self.saveCurrent()

            if correct:
                self.repaint()
                time.sleep(1)
                self.nextcard()
        else:
            if self.nowstate == 'new':
                self.failcards.append({'key': self.nowkey, 'time': datetime.datetime.now() + _failDelta,
                                       'ft': 1, 'only': False, 'ascore': score})
            elif self.nowstate == 'fail' or self.nowstate == 'onlyOne':
                self.cardstate['ft'] += 1
                self.cardstate['ascore'] += score
                self.failcards.append(
                    dict({'key': self.nowkey, 'time': datetime.datetime.now() + _failDelta}, **self.cardstate))
            self.label_5_setText(**self.failcards[-1], score=score)
            self.widget.show()
            self.pushButton.close()

            self.saveCurrent()

    def incognizance(self):
        self.inputConfirm(confirm=False)

    def saveOldRecords(self):
        if not os.path.exists('oldrecords'):
            os.mkdir('oldrecords')
        import shutil
        shutil.copyfile('records.xlsx', os.path.join(
            'oldrecords', datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') + '.xlsx'))

    def complete(self):
        self.saveOldRecords()
        font = QtGui.QFont()
        font.setPointSize(24)
        self.label.setFont(font)
        self.label.setText('已完成学习')
        self.lineEdit.close()
        self.textEdit.close()
        self.textEdit_2.close()
        self.textEdit_3.close()
        self.label_2.close()
        self.label_3.close()
        self.label_4.close()
        self.widget.close()
        self.pushButton.close()
        self.pushButton_2.close()
        self.surplus.close()

    def nextcard(self):
        if not self.keys and not self.failcards and not self.onlyones:
            self.complete()
            return
        nowtime = datetime.datetime.now() if self.keys else _maxDate
        failtime = self.failcards[0]['time'] if self.failcards else _maxDate
        onlytime = self.onlyones[0]['time'] if self.onlyones else _maxDate
        case = argmin(nowtime, failtime, onlytime)
        if case == 0: self.nowkey, self.nowstate, self.cardstate = self.keys.pop(0), 'new', None
        elif case == 1:
            self.cardstate, self.nowstate = self.failcards.pop(0), 'fail'
            self.nowkey = self.cardstate.pop('key')
            self.cardstate.pop('time')
        elif case == 2:
            self.cardstate, self.nowstate = self.onlyones.pop(0), 'onlyOne'
            self.nowkey = self.cardstate.pop('key')
            self.cardstate.pop('time')

        self.widget.close()
        self.pushButton.show()
        self.initOneCard(card=self.cards[self.nowkey])



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LearnNewCards()
    sys.exit(app.exec_())