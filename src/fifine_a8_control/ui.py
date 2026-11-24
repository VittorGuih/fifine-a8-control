import sys,ctypes,threading,queue,time
from ctypes import wintypes
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QRectF,QPointF,QSignalBlocker
from PySide6.QtGui import QPainter,QPainterPath,QColor,QPen,QFont,QFontDatabase
from PySide6.QtWidgets import QApplication,QWidget,QLabel,QPushButton,QVBoxLayout,QHBoxLayout,QFrame,QAbstractButton
from . import runtime as rt
INK='#1D1D1F';SECONDARY='#63636B';GREEN='#248A3D';RED='#D62C3A'

class AccentPolicy(ctypes.Structure):
    _fields_=[('state',ctypes.c_int),('flags',ctypes.c_int),('color',ctypes.c_uint),('animation',ctypes.c_int)]
class CompositionData(ctypes.Structure):
    _fields_=[('attribute',ctypes.c_int),('data',ctypes.c_void_p),('size',ctypes.c_size_t)]
class Margins(ctypes.Structure):
    _fields_=[('left',ctypes.c_int),('right',ctypes.c_int),('top',ctypes.c_int),('bottom',ctypes.c_int)]
def native_glass(hwnd):
    result={}
    try:
        u=ctypes.WinDLL('user32');d=ctypes.WinDLL('dwmapi')
        fn=u.SetWindowCompositionAttribute;fn.argtypes=[wintypes.HWND,ctypes.POINTER(CompositionData)];fn.restype=wintypes.BOOL
        policy=AccentPolicy(4,0x20|0x40|0x80|0x100,0x9CF8F6F3,0)
        data=CompositionData(19,ctypes.cast(ctypes.pointer(policy),ctypes.c_void_p),ctypes.sizeof(policy))
        result['acrylic']=bool(fn(hwnd,ctypes.byref(data)))
        d.DwmSetWindowAttribute.argtypes=[wintypes.HWND,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD]
        corner=ctypes.c_int(2);result['corner']=d.DwmSetWindowAttribute(hwnd,33,ctypes.byref(corner),4)
        dark=ctypes.c_int(0);d.DwmSetWindowAttribute(hwnd,20,ctypes.byref(dark),4)
        d.DwmExtendFrameIntoClientArea.argtypes=[wintypes.HWND,ctypes.POINTER(Margins)]
        m=Margins(-1,-1,-1,-1);result['shadow']=d.DwmExtendFrameIntoClientArea(hwnd,ctypes.byref(m))
    except Exception as e:result['error']=str(e)
    rt.log('GLASS',**result)
    return result.get('acrylic',False)

def mic_path(p,cx,cy,color,muted=False,scale=1):
    p.save();p.translate(cx,cy);p.scale(scale,scale);p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen);p.setBrush(QColor(color));p.drawRoundedRect(QRectF(-8,-22,16,29),8,8)
    p.setPen(QPen(QColor(color),2.6,Qt.SolidLine,Qt.RoundCap));p.setBrush(Qt.NoBrush)
    path=QPainterPath(QPointF(-14,-4));path.lineTo(-14,1);path.cubicTo(-14,20,14,20,14,1);path.lineTo(14,-4);p.drawPath(path)
    p.drawLine(QPointF(0,16),QPointF(0,25));p.drawLine(QPointF(-8,25),QPointF(8,25))
    if muted:
        p.setPen(QPen(QColor('#FBE9EC'),6,Qt.SolidLine,Qt.RoundCap));p.drawLine(QPointF(-22,22),QPointF(22,-22))
        p.setPen(QPen(QColor(color),2.5,Qt.SolidLine,Qt.RoundCap));p.drawLine(QPointF(-22,22),QPointF(22,-22))
    p.restore()
class Hero(QWidget):
    def __init__(self):super().__init__();self.state=None;self.setFixedSize(88,88)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        color=GREEN if self.state is False else RED if self.state is True else '#6F7580'
        tint=QColor('#E3F3E8' if self.state is False else '#FBE9EC' if self.state is True else '#EEF0F5');tint.setAlpha(210)
        p.setPen(QPen(QColor(255,255,255,230),1));p.setBrush(tint);p.drawRoundedRect(QRectF(2,2,84,84),25,25)
        mic_path(p,44,43,color,self.state is True)
class Switch(QAbstractButton):
    def __init__(self,name):
        super().__init__();self.setCheckable(True);self.setFixedSize(46,28);self.setAccessibleName(name);self.setCursor(Qt.PointingHandCursor)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        fill=QColor('#34C759' if self.isChecked() else '#BFC4CD');fill.setAlpha(255 if self.isEnabled() else 90)
        p.setBrush(fill);p.setPen(Qt.NoPen);p.drawRoundedRect(QRectF(1,2,44,25),12.5,12.5)
        x=23 if self.isChecked() else 3
        p.setBrush(QColor(0,0,0,25));p.drawEllipse(QRectF(x,4,21,21));p.setBrush(QColor('white'));p.drawEllipse(QRectF(x,3,21,21))
        if self.hasFocus():p.setBrush(Qt.NoBrush);p.setPen(QPen(QColor('#007AFF'),1));p.drawRoundedRect(QRectF(.5,.5,45,27),13,13)
class TitleBar(QWidget):
    def __init__(self,owner):
        super().__init__();self.owner=owner;layout=QHBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(7)
        label=QLabel('Fifine A8');label.setObjectName('brand');label.setAttribute(Qt.WA_TransparentForMouseEvents);layout.addWidget(label);layout.addStretch()
        self.badge=QLabel('●  Connecting');self.badge.setObjectName('badge');layout.addWidget(self.badge);layout.addSpacing(7)
        mini=QPushButton('−');mini.setObjectName('windowControl');mini.setFixedSize(26,26);mini.setAccessibleName('Minimize');mini.clicked.connect(owner.showMinimized);layout.addWidget(mini)
        close=QPushButton('×');close.setObjectName('closeControl');close.setFixedSize(26,26);close.setAccessibleName('Close');close.clicked.connect(owner.close);layout.addWidget(close)
    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton and self.owner.windowHandle():self.owner.windowHandle().startSystemMove()
class App(QWidget):
    def __init__(self, demo=False):
        super().__init__();self.setWindowTitle('Fifine A8 — Control');self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowSystemMenuHint|Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground);self.setFixedSize(480,600);self.glass=False
        self.demo=demo;self.busy=False;self.ready=False;self.desired=None;self.confirmed=None;self.pending=False;self.count=0;self.errors=0;self.connected=False;self.mode='starting';self.last_touch=''
        self.setStyleSheet('''
            QWidget { color:#1D1D1F; font-size:13px; background:transparent; }
            QLabel#brand {font-size:16px;font-weight:600;letter-spacing:-0.3px;}
            QLabel#badge {background:rgba(255,255,255,110);border:1px solid rgba(255,255,255,130);border-radius:11px;padding:4px 8px;font-size:10px;color:#5D6470;}
            QPushButton#windowControl,QPushButton#closeControl {border:0;border-radius:13px;font-size:20px;color:#606571;}
            QPushButton#windowControl:hover {background:rgba(255,255,255,150);}
            QPushButton#closeControl:hover {background:#FF6058;color:white;}
            QLabel#status {font-size:27px;font-weight:600;letter-spacing:-0.8px;}
            QLabel#detail {color:#646873;font-size:12px;}
            QFrame#segments {background:rgba(186,194,209,95);border:1px solid rgba(255,255,255,175);border-radius:18px;}
            QPushButton[stateButton="true"] {font-size:14px;font-weight:600;border:1px solid transparent;border-radius:13px;color:#515866;background:transparent;padding:13px 0;}
            QPushButton[stateButton="true"]:hover {background:rgba(255,255,255,100);}
            QPushButton[stateButton="true"]:disabled {color:#969CA6;}
            QPushButton[stateButton="true"]:focus {border:1px solid #007AFF;}
            QFrame#settings {background:rgba(255,255,255,105);border:1px solid rgba(255,255,255,185);border-radius:18px;}
            QLabel#rowTitle {font-weight:600;font-size:13px;}
            QLabel#rowSubtitle {color:#676E7A;font-size:10px;}
            QLabel#footer {color:#747A87;font-size:10px;}
            QLabel#lockBadge {color:#747A87;font-size:10px;background:rgba(255,255,255,85);border-radius:9px;padding:3px 8px;}
        ''')
        layout=QVBoxLayout(self);layout.setContentsMargins(26,18,26,20);layout.setSpacing(0)
        self.titlebar=TitleBar(self);layout.addWidget(self.titlebar);layout.addSpacing(22)
        self.hero=Hero();layout.addWidget(self.hero,0,Qt.AlignHCenter);layout.addSpacing(16)
        self.status=QLabel('Connecting…');self.status.setObjectName('status');self.status.setAlignment(Qt.AlignCenter);layout.addWidget(self.status)
        self.detail=QLabel('Looking for your microphone.');self.detail.setObjectName('detail');self.detail.setWordWrap(True);self.detail.setAlignment(Qt.AlignCenter);self.detail.setMinimumHeight(42);layout.addWidget(self.detail);layout.addSpacing(18)
        segments=QFrame();segments.setObjectName('segments');sl=QHBoxLayout(segments);sl.setContentsMargins(5,5,5,5);sl.setSpacing(5)
        self.unmute=QPushButton('Activate');self.unmute.setProperty('stateButton',True);self.unmute.setMinimumHeight(53);self.unmute.setAccessibleName('Activate microphone');self.unmute.clicked.connect(lambda:self.choose(False));sl.addWidget(self.unmute,1)
        self.mute=QPushButton('Mute');self.mute.setProperty('stateButton',True);self.mute.setMinimumHeight(53);self.mute.setAccessibleName('Mute microphone');self.mute.clicked.connect(lambda:self.choose(True));sl.addWidget(self.mute,1)
        layout.addWidget(segments);layout.addSpacing(22)
        settings=QFrame();settings.setObjectName('settings');cl=QVBoxLayout(settings);cl.setContentsMargins(18,17,18,17);cl.setSpacing(13)
        self.lock=Switch('Keep selected state');self.lock.toggled.connect(self.lock_changed)
        self.add_setting(cl,'Keep selected state','Also overrides intentional physical presses.',self.lock)
        divider=QFrame();divider.setFixedHeight(1);divider.setStyleSheet('background:rgba(112,123,142,25);border:0;');cl.addWidget(divider)
        self.top=Switch('Always on top');self.top.toggled.connect(self.top_changed)
        self.add_setting(cl,'Always on top','Keep this window above other apps.',self.top)
        layout.addWidget(settings);layout.addStretch(1);layout.addSpacing(16)
        footer=QHBoxLayout();self.activity=QLabel('No button events yet');self.activity.setObjectName('footer');footer.addWidget(self.activity);footer.addStretch()
        self.lock_badge=QLabel('Manual');self.lock_badge.setObjectName('lockBadge');footer.addWidget(self.lock_badge);layout.addLayout(footer)
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(40);self.render()
        if not self.demo:
            threading.Thread(target=rt.backend,daemon=True).start();threading.Thread(target=rt.monitor,daemon=True).start()
        else:
            self.connected=True;self.ready=True;self.mode='idle';self.render()
        QTimer.singleShot(50,self.apply_material)
    def add_setting(self,layout,title,subtitle,switch):
        row=QHBoxLayout();row.setContentsMargins(0,0,0,0);row.setSpacing(12);text=QVBoxLayout();text.setSpacing(3)
        a=QLabel(title);a.setObjectName('rowTitle');text.addWidget(a);b=QLabel(subtitle);b.setObjectName('rowSubtitle');text.addWidget(b)
        row.addLayout(text,1);row.addWidget(switch);layout.addLayout(row)
    def apply_material(self):self.glass=native_glass(int(self.winId()));self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        path=QPainterPath();path.addRoundedRect(QRectF(.5,.5,self.width()-1,self.height()-1),22,22)
        p.setClipPath(path);p.fillPath(path,QColor(246,248,253,30 if self.glass else 238))
        p.setPen(QPen(QColor(255,255,255,170),1));p.setBrush(Qt.NoBrush);p.drawPath(path)
    def set_switch(self,switch,value):
        blocker=QSignalBlocker(switch);switch.setChecked(value);del blocker
    def top_changed(self,on):
        self.setWindowFlag(Qt.WindowStaysOnTopHint,on);self.show();QTimer.singleShot(30,self.apply_material)
    def choose(self,muted):
        if self.busy or not self.ready or not self.connected:return
        self.desired=muted;self.send()
    def send(self):
        if self.busy or self.desired is None or not self.ready:return
        self.busy=True;self.render()
        if self.demo:
            QTimer.singleShot(150,lambda:rt.events.put(('response',{'ok':True,'muted':self.desired})))
        else:rt.commands.put('mute' if self.desired else 'unmute')
    def lock_changed(self,on):
        rt.log('LOCK',enabled=on,desired_muted=self.desired);self.render()
        if on and self.desired is not None:self.send()
    def render(self):
        known=self.mode=='applied' and self.confirmed is not None and not self.busy
        self.hero.state=self.confirmed if known else None;self.hero.update()
        for button,muted in [(self.unmute,False),(self.mute,True)]:
            active=known and self.confirmed is muted
            button.setText(('✓  Muted' if muted else '✓  Active') if active else ('Mute' if muted else 'Activate'))
            button.setEnabled(self.ready and self.connected and not self.busy)
            color=RED if muted else GREEN
            button.setStyleSheet(('background:'+color+';color:white;border:1px solid rgba(255,255,255,100);') if active else '')
            button.setAccessibleDescription('Selected state' if active else 'Apply this state')
        self.lock.setEnabled(self.ready and self.connected and self.desired is not None)
        self.titlebar.badge.setText('Preview' if self.demo else ('●  Connected' if self.connected else '●  Offline'))
        self.titlebar.badge.setStyleSheet('color:'+('#247B46' if self.connected else '#747A87')+';')
        self.lock_badge.setText('State pinned' if self.lock.isChecked() else 'Manual')
        if self.busy:title='Applying…';detail='Sending your choice to the A8.'
        elif self.mode=='applied':
            title='Microphone muted' if self.confirmed else 'Microphone active'
            detail='Your choice will be reapplied automatically.' if self.lock.isChecked() else 'Command applied to A8. LED: '+('red.' if self.confirmed else 'green.')
        elif self.mode=='physical':title='Physical button pressed';detail='Reapply a choice to confirm the state.'
        elif self.mode=='error':title='Check your microphone';detail=getattr(self,'error_text','Reconnect the FIFINE A8.')
        elif self.mode=='starting':title='Connecting…';detail='Looking for your microphone.'
        else:title='Choose a state';detail='Activate or mute your microphone.'
        if self.demo:detail='Preview mode — no device commands are sent.'
        self.status.setText(title);self.detail.setText(detail)
    def tick(self):
        try:
            while True:
                kind,data=rt.events.get_nowait()
                if kind=='ready':
                    self.ready=bool(data.get('ok'));self.mode='idle' if self.ready else 'error'
                    if not self.ready:self.error_text=data.get('error','Reconnect the A8.')
                elif kind=='response':
                    self.busy=False
                    if data.get('ok'):self.errors=0;self.confirmed=data['muted'];self.mode='applied'
                    else:
                        self.errors+=1;self.confirmed=None;self.mode='error';self.error_text=data.get('error','Could not apply the command.')
                        if self.errors>=3:self.set_switch(self.lock,False);self.pending=False
                    if self.pending and self.lock.isChecked():self.pending=False;QTimer.singleShot(80,self.send)
                elif kind=='button':
                    self.count+=1;self.last_touch=data;self.activity.setText(f'{self.count} toque'+('s' if self.count!=1 else '')+f'  ·  {data}')
                    if self.lock.isChecked() and self.desired is not None:
                        if self.busy:self.pending=True
                        else:self.send()
                    else:
                        self.confirmed=None
                        if not self.busy:self.mode='physical'
                elif kind=='availability':
                    was_ready=self.ready;self.ready=bool(data.get('ok'))
                    if not self.ready:
                        self.confirmed=None;self.pending=False;self.set_switch(self.lock,False);self.mode='error';self.error_text=data.get('error','Reconnect the A8.')
                    elif not was_ready:self.mode='idle'
                elif kind=='connected':self.connected=True
                elif kind=='device_error':self.connected=False;self.confirmed=None;self.set_switch(self.lock,False);self.mode='error';self.error_text='Reconnect the FIFINE A8.'
                elif kind=='error':self.ready=False;self.busy=False;self.confirmed=None;self.set_switch(self.lock,False);self.mode='error';self.error_text=data
                self.render()
        except queue.Empty:pass
    def closeEvent(self,event):
        rt.closing.set();rt.log('CLOSE');self.timer.stop();event.accept()

def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description="Control the FIFINE A8 physical mute and LED on Windows.")
    parser.add_argument("--debug",action="store_true",help="Write optional local event logs (no audio).")
    parser.add_argument("--demo",action="store_true",help="Preview the interface without accessing a device.")
    args=parser.parse_args(argv)
    if sys.platform!="win32" and not args.demo:
        parser.error("Hardware control currently supports Windows only.")
    if args.debug:rt.enable_debug()
    app=QApplication(sys.argv[:1]);app.setApplicationName("Fifine A8 Control")
    families=QFontDatabase.families()
    family=next((x for x in ["SF Pro Display","SF Pro Text","Segoe UI Variable","Segoe UI"] if x in families),"Segoe UI")
    app.setFont(QFont(family,10))
    mutex=None
    if sys.platform=="win32" and not args.demo:
        from PySide6.QtWidgets import QMessageBox
        kernel=ctypes.WinDLL("kernel32",use_last_error=True)
        kernel.CreateMutexW.argtypes=[ctypes.c_void_p,wintypes.BOOL,wintypes.LPCWSTR]
        kernel.CreateMutexW.restype=wintypes.HANDLE
        mutex=kernel.CreateMutexW(None,False,"Local\\FifineA8Control")
        if ctypes.get_last_error()==183:
            QMessageBox.information(None,"Fifine A8 Control","The app is already open. Use its existing window.")
            return 0
    rt.log("OPEN",ui="Qt Acrylic",demo=args.demo)
    window=App(demo=args.demo);window.show()
    result=app.exec();time.sleep(.3)
    if mutex:
        kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle(mutex)
    return result
