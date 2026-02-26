import sys
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QPushButton)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QColor
from datetime import datetime

class IndexNotifier(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("리나의 지수 통합 알리미 🦞")
        self.setMinimumSize(600, 400)
        self.init_ui()
        
        # 타이머 설정 (30초마다 업데이트)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(30000)
        
        # 초기 데이터 로드
        self.update_data()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 헤더 레이블
        self.header_label = QLabel("실시간 지수 모니터링")
        self.header_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_label)

        # 시간 표시
        self.time_label = QLabel("마지막 업데이트: --:--:--")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.time_label)

        # 테이블 설정
        self.table = QTableWidget(7, 3)
        self.table.setHorizontalHeaderLabels(["지수명", "현재가", "등락율"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # 수동 업데이트 버튼
        self.refresh_btn = QPushButton("지금 업데이트")
        self.refresh_btn.clicked.connect(self.update_data)
        layout.addWidget(self.refresh_btn)

        # 지수 목록 초기화
        self.indices = [
            ("나스닥 100 선물", "NQ=F"),
            ("S&P 500 선물", "ES=F"),
            ("다우 선물", "YM=F"),
            ("코스피 지수", "^KS11"),
            ("코스닥 지수", "^KQ11"),
            ("필라델피아 반도체", "^SOX"),
            ("국내 야간선물", "KR_NIGHT")
        ]

    def get_yfinance_data(self, ticker):
        try:
            t = yf.Ticker(ticker)
            data = t.history(period="1d", interval="1m")
            if data.empty:
                # 데이터가 비어있으면 info에서 가져오기 시도
                current = t.info.get('regularMarketPrice') or t.info.get('currentPrice')
                prev = t.info.get('previousClose')
            else:
                current = data['Close'].iloc[-1]
                # history 데이터가 충분하지 않을 수 있으므로 info의 previousClose 활용
                prev = t.info.get('previousClose') or data['Open'].iloc[0]
            
            if current and prev:
                change_pct = ((current - prev) / prev) * 100
                return f"{current:,.2f}", f"{change_pct:+.2f}%", change_pct
            return "N/A", "N/A", 0
        except:
            return "Error", "Error", 0

    def get_kr_night_futures(self):
        """esignal.co.kr에서 야간선물 데이터 파싱 시도 (단순 텍스트 기반)"""
        url = "http://esignal.co.kr/kospi200-futures-night/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            # 이 사이트는 데이터가 동적으로 들어오지만, 초기 HTML에 '현재가' 앵커가 있음
            # 실제 값은 셀레늄이나 소켓이 필요할 수 있으나 MVP로 기본 크롤링 시도
            resp = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # ttime 클래스 등을 확인하여 데이터 갱신 여부 체크 가능
            # 현재는 사이트 구조상 직접적인 실시간 값 추출에 한계가 있을 수 있음을 고지
            return "연결됨", "대기중", 0
        except:
            return "오류", "오류", 0

    def update_data(self):
        self.time_label.setText(f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
        
        for i, (name, ticker) in enumerate(self.indices):
            if ticker == "KR_NIGHT":
                price, pct_str, pct_val = self.get_kr_night_futures()
            else:
                price, pct_str, pct_val = self.get_yfinance_data(ticker)

            # 이름
            self.table.setItem(i, 0, QTableWidgetItem(name))
            
            # 가격
            price_item = QTableWidgetItem(price)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 1, price_item)
            
            # 등락율 및 색상
            pct_item = QTableWidgetItem(pct_str)
            pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if pct_val > 0:
                pct_item.setForeground(QColor("red"))
            elif pct_val < 0:
                pct_item.setForeground(QColor("blue"))
            self.table.setItem(i, 2, pct_item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IndexNotifier()
    window.show()
    sys.exit(app.exec())
