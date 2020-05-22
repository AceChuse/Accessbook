from learncard import *


_maxDate = datetime.datetime(datetime.MAXYEAR, month=12, day=31)
_minDate = datetime.datetime(datetime.MINYEAR, month=1, day=1)

_reviewfailDelta = datetime.timedelta(minutes = 10)


class ReviewCards(LearnNewCards):
    def __init__(self):

        super().__init__()

    def init(self):
        today = datetime.date.today()

        if os.path.exists('reviewCardKeys.xlsx'):
            self.keys = pd.read_excel('reviewCardKeys.xlsx', sheet_name=0).to_dict(orient='list')['key']
        else:
            self.keys = []

        if os.path.exists('reviewCardFailCards.xlsx'):
            self.failcards = pd.read_excel('reviewCardFailCards.xlsx', sheet_name=0
                                           ).to_dict(orient='records')
        else: self.failcards = []

        if not self.keys and not self.failcards:
            self.keys = [record[0] for record in self.records.items() if record[1]['date'].date() <= today]

        print([self.cards[key] for key in self.keys])
        print('keys', self.keys)
        print('failcards', self.failcards)
        self.title = "Review cards."
        if len(self.keys) + len(self.failcards) == 0:
            self.initUI = self.initpass
            self.setupUi(self)
            self.show()
            self.complete()

    def initpass(self):
        pass

    def count(self):
        return len(self.keys) + len(self.failcards) + 1

    def saveCurrent(self):
        #save current keys
        df = pd.DataFrame(self.keys, columns=['key'])
        df.to_excel('reviewCardKeys.xlsx')
        #save current failcards
        df = pd.DataFrame(self.failcards, columns=['key', 'time', 'ft', 'ascore', 'firstscore'])
        writer = pd.ExcelWriter('reviewCardFailCards.xlsx')
        df.to_excel(writer, sheet_name='Sheet1')
        writer.sheets['Sheet1'].set_column('B:B', 15)
        writer.sheets['Sheet1'].set_column('C:C', 25)
        writer.sheets['Sheet1'].set_column('D:E', 8)
        writer.sheets['Sheet1'].set_column('F:F', 16)

    def label_5_setText(self, **kwargs):
        date = kwargs.get('date')
        if date is None: kwargs['time'] = kwargs['time'].strftime('%Y/%m/%d %H:%M:%S')
        else: kwargs['date'] = date.strftime('%Y/%m/%d %H:%M:%S')
        self.label_5.setText(str(kwargs))

    def dealResult(self, correct, score, if_pass=False):
        print('here1')
        if correct or if_pass:
            #quality = (self.cardstate['ascore'] + score) / (self.cardstate['ft'] + 1)
            quality = self.cardstate['firstscore']
            quality = score if quality is None else quality
            record = self.records.get(self.nowkey)
            print('here2', record)
            if record is None:
                raise Exception('This card has not been learned!')
            else:
                self.records[self.nowkey] = ankiAlgorithm(
                    quality=quality, repetitions=record['rep'],
                    easiness=record['ef'], interval=record['interval'])
            #self.label_5.setText(str(self.records[self.nowkey]))
            self.label_5_setText(**self.records[self.nowkey], score=score)
            self.widget.show()
            self.pushButton.close()

            print('here4', quality, self.records[self.nowkey])
            self.saveRecord()
            print('here5')
            self.saveCurrent()
            print('here6')

            if correct:
                self.repaint()
                time.sleep(1)
                self.nextcard(saveold=True)
        else:
            if self.nowstate == 'new':
                self.failcards.append({'key': self.nowkey, 'time': datetime.datetime.now() + _reviewfailDelta,
                                       'ft': 1, 'ascore': score, 'firstscore': score})
            elif self.nowstate == 'fail':
                self.cardstate['ft'] += 1
                self.cardstate['ascore'] += score
                self.failcards.append(
                    dict({'key': self.nowkey, 'time': datetime.datetime.now() + _reviewfailDelta}, **self.cardstate))
            self.label_5_setText(**self.failcards[-1], score=score)
            self.widget.show()
            self.pushButton.close()

            self.saveCurrent()

    def complete(self):
        self.saveOldRecords()
        font = QtGui.QFont()
        font.setPointSize(24)
        self.label.setFont(font)
        self.label.setText('已完成复习')
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

    def nextcard(self, saveold=False):
        if not self.keys and not self.failcards and saveold:
            self.complete()
            return
        nowtime = datetime.datetime.now() if self.keys else _maxDate
        failtime = self.failcards[0]['time'] if self.failcards else _maxDate
        case = argmin(nowtime, failtime)
        if case == 0: self.nowkey, self.nowstate, self.cardstate = \
            self.keys.pop(0), 'new', {'ft': 0, 'ascore': 0, 'firstscore': None}
        elif case == 1:
            self.cardstate, self.nowstate = self.failcards.pop(0), 'fail'
            self.nowkey = self.cardstate.pop('key')
            self.cardstate.pop('time')

        self.widget.close()
        self.pushButton.show()
        self.initOneCard(card=self.cards[self.nowkey])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ReviewCards()
    sys.exit(app.exec_())