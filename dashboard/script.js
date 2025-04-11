// 전역 변수
let signalsChart = null;
let config = null;

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    // 데이터 로드
    loadData();
    
    // 새로고침 버튼 이벤트
    document.getElementById('refresh-btn').addEventListener('click', loadData);
    
    // 차트 기간 변경 이벤트
    document.getElementById('chart-days').addEventListener('change', function() {
        loadChartData(this.value);
    });
});

// 전체 데이터 로드
async function loadData() {
    try {
        // 설정 파일 로드
        await loadConfig();
        
        // 현재 트레이딩 로그 로드
        await loadTradingLogs();
        
        // 차트 데이터 로드 (기본 7일)
        await loadChartData(7);
        
        // 최종 업데이트 시간 표시
        document.getElementById('last-updated').textContent = '업데이트: ' + new Date().toLocaleString();
    } catch (error) {
        console.error('데이터 로드 오류:', error);
        alert('데이터 로드 중 오류가 발생했습니다.');
    }
}

// 설정 파일 로드
async function loadConfig() {
    try {
        // config/trading_config.py 파일 로드
        const configResponse = await fetch('../config/trading_config.py');
        const configText = await configResponse.text();
        
        // 파이썬 설정 파일 파싱 (간단하게 처리)
        config = parseConfigFile(configText);
        
        // 설정 표시
        displayConfig(config);
    } catch (error) {
        console.error('설정 로드 오류:', error);
    }
}

// 파이썬 설정 파일 파싱 (간단한 구현)
function parseConfigFile(configText) {
    const config = {};
    
    // DECISION_THRESHOLDS 파싱
    const decisionThresholdsMatch = configText.match(/DECISION_THRESHOLDS\s*=\s*{([^}]*)}/s);
    if (decisionThresholdsMatch) {
        config.DECISION_THRESHOLDS = parseDict(decisionThresholdsMatch[1]);
    }
    
    // INVESTMENT_RATIOS 파싱
    const investmentRatiosMatch = configText.match(/INVESTMENT_RATIOS\s*=\s*{([^}]*)}/s);
    if (investmentRatiosMatch) {
        config.INVESTMENT_RATIOS = parseDict(investmentRatiosMatch[1]);
    }
    
    // SIGNAL_STRENGTHS 파싱
    const signalStrengthsMatch = configText.match(/SIGNAL_STRENGTHS\s*=\s*{([^}]*)}/s);
    if (signalStrengthsMatch) {
        config.SIGNAL_STRENGTHS = parseDict(signalStrengthsMatch[1]);
    }
    
    // INDICATOR_WEIGHTS 파싱
    const indicatorWeightsMatch = configText.match(/INDICATOR_WEIGHTS\s*=\s*{([^}]*)}/s);
    if (indicatorWeightsMatch) {
        config.INDICATOR_WEIGHTS = parseDict(indicatorWeightsMatch[1]);
    }
    
    // INDICATOR_USAGE 파싱
    const indicatorUsageMatch = configText.match(/INDICATOR_USAGE\s*=\s*{([^}]*)}/s);
    if (indicatorUsageMatch) {
        config.INDICATOR_USAGE = parseDict(indicatorUsageMatch[1]);
    }
    
    // TRADING_SETTINGS 파싱
    const tradingSettingsMatch = configText.match(/TRADING_SETTINGS\s*=\s*{([^}]*)}/s);
    if (tradingSettingsMatch) {
        config.TRADING_SETTINGS = parseDict(tradingSettingsMatch[1]);
    }
    
    return config;
}

// Python 딕셔너리 문자열 파싱
function parseDict(dictStr) {
    const result = {};
    const entries = dictStr.split(',');
    
    for (let entry of entries) {
        entry = entry.trim();
        if (!entry) continue;
        
        // 주석 제거
        entry = entry.split('#')[0].trim();
        if (!entry) continue;
        
        const match = entry.match(/["']?([^:"']+)["']?\s*:\s*([^,]+)/);
        if (match) {
            const key = match[1].trim();
            let value = match[2].trim();
            
            // Boolean, 숫자, 문자열 변환
            if (value === 'True') value = true;
            else if (value === 'False') value = false;
            else if (!isNaN(parseFloat(value))) value = parseFloat(value);
            else if (value.startsWith('"') || value.startsWith("'")) {
                value = value.slice(1, -1);
            }
            
            result[key] = value;
        }
    }
    
    return result;
}

// 설정 정보 표시
function displayConfig(config) {
    if (!config) return;
    
    // 결정 임계값
    let thresholdsHtml = '';
    for (const [key, value] of Object.entries(config.DECISION_THRESHOLDS || {})) {
        thresholdsHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
            ${formatConfigKey(key)}
            <span>${value}</span>
        </li>`;
    }
    document.getElementById('decision-thresholds').innerHTML = thresholdsHtml || '<li class="list-group-item">데이터 없음</li>';
    
    // 투자 비율
    let ratiosHtml = '';
    for (const [key, value] of Object.entries(config.INVESTMENT_RATIOS || {})) {
        ratiosHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
            ${formatConfigKey(key)}
            <span>${value * 100}%</span>
        </li>`;
    }
    document.getElementById('investment-ratios').innerHTML = ratiosHtml || '<li class="list-group-item">데이터 없음</li>';
    
    // 지표 사용 여부
    let usageHtml = '';
    for (const [key, value] of Object.entries(config.INDICATOR_USAGE || {})) {
        usageHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
            ${key}
            <span class="badge ${value ? 'bg-success' : 'bg-secondary'}">${value ? '사용' : '미사용'}</span>
        </li>`;
    }
    document.getElementById('indicator-usage').innerHTML = usageHtml || '<li class="list-group-item">데이터 없음</li>';
    
    // 매매 관련 설정
    let tradingHtml = '';
    for (const [key, value] of Object.entries(config.TRADING_SETTINGS || {})) {
        if (typeof value === 'object') continue; // 중첩 객체는 건너뜀
        tradingHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
            ${formatConfigKey(key)}
            <span>${value}</span>
        </li>`;
    }
    document.getElementById('trading-settings').innerHTML = tradingHtml || '<li class="list-group-item">데이터 없음</li>';
    
    // 지표 가중치
    let weightsHtml = '';
    for (const [key, value] of Object.entries(config.INDICATOR_WEIGHTS || {})) {
        weightsHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
            ${key}
            <span>${value}</span>
        </li>`;
    }
    document.getElementById('indicator-weights').innerHTML = weightsHtml || '<li class="list-group-item">데이터 없음</li>';
    
    // 신호 강도
    let strengthsHtml = '';
    const topStrengths = Object.entries(config.SIGNAL_STRENGTHS || {})
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10); // 상위 10개만 표시
    
    for (const [key, value] of topStrengths) {
        strengthsHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
            ${formatConfigKey(key)}
            <span>${value}</span>
        </li>`;
    }
    document.getElementById('signal-strengths').innerHTML = strengthsHtml || '<li class="list-group-item">데이터 없음</li>';
}

// 설정 키 포맷팅
function formatConfigKey(key) {
    return key.replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// 트레이딩 로그 로드
async function loadTradingLogs() {
    try {
        // 오늘 날짜 구하기
        const today = new Date().toISOString().split('T')[0].replace(/-/g, '');
        
        // 로그 파일 로드
        const response = await fetch(`../logs/trading_log_${today}.json`);
        
        // 응답 확인
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const logs = await response.json();
        
        // 로그가 없으면
        if (!logs || logs.length === 0) {
            document.getElementById('trading-logs').innerHTML = '<tr><td colspan="2" class="text-center">로그 데이터가 없습니다.</td></tr>';
            document.getElementById('signals-table').innerHTML = '<tr><td colspan="4" class="text-center">신호 데이터가 없습니다.</td></tr>';
            return;
        }
        
        // 최근 로그 (가장 최신 데이터)
        const latestLog = logs[logs.length - 1];
        
        // 현재 상태 업데이트
        updateCurrentStatus(latestLog);
        
        // 지표 요약 표시
        updateIndicatorsSummary(latestLog);
        
        // 신호 테이블 업데이트
        updateSignalsTable(latestLog);
        
        // 거래 로그 표시
        updateTradingLogs(logs);
        
        // 거래 기록 로드
        loadTradeHistory();
    } catch (error) {
        console.error('트레이딩 로그 로드 오류:', error);
        document.getElementById('trading-logs').innerHTML = '<tr><td colspan="2" class="text-center">로그 데이터를 불러올 수 없습니다.</td></tr>';
    }
}

// 현재 상태 업데이트
function updateCurrentStatus(latestLog) {
    if (!latestLog) return;
    
    // 현재가 설정
    const currentPrice = latestLog.current_price?.[0]?.trade_price;
    if (currentPrice) {
        document.getElementById('current-price').textContent = formatKRW(currentPrice);
    } else {
        document.getElementById('current-price').textContent = '데이터 없음';
    }
    
    // 가격 변화율
    const priceChange = latestLog.price_change_24h;
    const priceChangeElement = document.getElementById('price-change');
    
    if (priceChange && priceChange !== 'N/A') {
        priceChangeElement.textContent = priceChange;
        
        if (priceChange.startsWith('-')) {
            priceChangeElement.className = 'badge down';
        } else {
            priceChangeElement.className = 'badge up';
        }
    } else {
        priceChangeElement.textContent = 'N/A';
        priceChangeElement.className = 'badge bg-secondary';
    }
    
    // 거래 결정
    const decision = latestLog.decision;
    const decisionKr = latestLog.decision_kr || decision;
    const decisionElement = document.getElementById('trading-decision');
    
    if (decision) {
        decisionElement.textContent = decisionKr;
        
        if (decision === 'buy') {
            decisionElement.className = 'badge badge-buy';
        } else if (decision === 'sell') {
            decisionElement.className = 'badge badge-sell';
        } else {
            decisionElement.className = 'badge badge-hold';
        }
    } else {
        decisionElement.textContent = '데이터 없음';
        decisionElement.className = 'badge bg-secondary';
    }
    
    // 신뢰도
    const confidence = latestLog.confidence;
    if (confidence) {
        const percent = (confidence * 100).toFixed(1);
        document.getElementById('confidence-bar').style.width = `${percent}%`;
        document.getElementById('confidence-bar').textContent = `${percent}%`;
        
        // 색상 설정
        const confidenceBar = document.getElementById('confidence-bar');
        if (confidence < 0.3) {
            confidenceBar.className = 'progress-bar bg-danger';
        } else if (confidence < 0.5) {
            confidenceBar.className = 'progress-bar bg-warning';
        } else if (confidence < 0.7) {
            confidenceBar.className = 'progress-bar bg-info';
        } else {
            confidenceBar.className = 'progress-bar bg-success';
        }
    }
    
    // 신호 비율
    const signalCounts = latestLog.signal_counts;
    if (signalCounts) {
        document.getElementById('signal-ratio').textContent = 
            `${signalCounts.buy || 0}/${signalCounts.sell || 0}/${signalCounts.hold || 0}`;
    }
}

// 지표 요약 업데이트
function updateIndicatorsSummary(latestLog) {
    if (!latestLog || !latestLog.signals) return;
    
    const signals = latestLog.signals;
    let summaryHtml = '';
    
    // 주요 지표만 선택 (예시)
    const keyIndicators = ['RSI(상대강도지수)', '이동평균선(MA)', 'MACD', '볼린저밴드(BB)', '김프(한국 프리미엄)', '시장심리(공포&탐욕지수)'];
    
    for (const indicator of keyIndicators) {
        const signal = signals.find(s => s.source === indicator);
        
        if (signal) {
            let signalClass = '';
            if (signal.signal === 'buy') signalClass = 'signal-buy';
            else if (signal.signal === 'sell') signalClass = 'signal-sell';
            else signalClass = 'signal-hold';
            
            summaryHtml += `<tr>
                <td>${indicator}</td>
                <td class="${signalClass}">${getSignalEmoji(signal.signal)} ${translateSignal(signal.signal)}</td>
                <td>${signal.description}</td>
            </tr>`;
        }
    }
    
    document.getElementById('indicators-summary').innerHTML = summaryHtml || '<tr><td colspan="3" class="text-center">데이터 없음</td></tr>';
}

// 신호 테이블 업데이트
function updateSignalsTable(latestLog) {
    if (!latestLog || !latestLog.signals) return;
    
    const signals = latestLog.signals;
    let tableHtml = '';
    
    for (const signal of signals) {
        let signalClass = '';
        if (signal.signal === 'buy') signalClass = 'signal-buy';
        else if (signal.signal === 'sell') signalClass = 'signal-sell';
        else signalClass = 'signal-hold';
        
        // 신호 강도 바 색상
        let strengthBarClass = 'bg-secondary';
        if (signal.signal === 'buy') strengthBarClass = 'bg-success';
        else if (signal.signal === 'sell') strengthBarClass = 'bg-danger';
        
        tableHtml += `<tr>
            <td>${signal.source}</td>
            <td class="${signalClass}">
                ${getSignalEmoji(signal.signal)} ${translateSignal(signal.signal)}
            </td>
            <td>
                <div class="d-flex align-items-center">
                    <span class="me-2">${signal.strength?.toFixed(1) || 0}</span>
                    <div class="w-100 strength-bar ${strengthBarClass}" style="width: ${(signal.strength || 0) * 100}%"></div>
                </div>
            </td>
            <td>${signal.description}</td>
        </tr>`;
    }
    
    document.getElementById('signals-table').innerHTML = tableHtml || '<tr><td colspan="4" class="text-center">신호 데이터가 없습니다.</td></tr>';
}

// 거래 로그 업데이트
function updateTradingLogs(logs) {
    if (!logs || logs.length === 0) return;
    
    // 최근 10개 로그만 표시
    const recentLogs = logs.slice(-10).reverse();
    let logsHtml = '';
    
    for (const log of recentLogs) {
        const time = log.timestamp || '';
        
        let decisionClass = '';
        if (log.decision === 'buy') decisionClass = 'signal-buy';
        else if (log.decision === 'sell') decisionClass = 'signal-sell';
        else decisionClass = 'signal-hold';
        
        logsHtml += `<tr>
            <td>${time}</td>
            <td class="${decisionClass}">${getSignalEmoji(log.decision)} ${log.decision_kr || translateSignal(log.decision)} (${(log.confidence * 100).toFixed(1)}%)</td>
        </tr>`;
    }
    
    document.getElementById('trading-logs').innerHTML = logsHtml || '<tr><td colspan="2" class="text-center">로그 데이터가 없습니다.</td></tr>';
}

// 거래 기록 로드
async function loadTradeHistory() {
    try {
        // 오늘 날짜 구하기
        const today = new Date().toISOString().split('T')[0].replace(/-/g, '');
        
        // 거래 기록 로드 시도
        const response = await fetch(`../logs/trade_history_${today}.json`);
        
        // 파일이 없으면 trade.log 로드
        if (!response.ok) {
            const logResponse = await fetch('../logs/trade.log');
            if (!logResponse.ok) {
                document.getElementById('trade-history').innerHTML = '<tr><td colspan="3" class="text-center">거래 기록이 없습니다.</td></tr>';
                return;
            }
            
            const logText = await logResponse.text();
            const logLines = logText.split('\n').filter(line => line.trim() !== '');
            
            // 로그 파싱
            let historyHtml = '';
            
            for (const line of logLines.slice(-10).reverse()) {
                const match = line.match(/(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - (.+)/);
                if (match) {
                    const [_, timestamp, logType, level, message] = match;
                    
                    historyHtml += `<tr>
                        <td>${timestamp}</td>
                        <td>${level}</td>
                        <td>${message}</td>
                    </tr>`;
                }
            }
            
            document.getElementById('trade-history').innerHTML = historyHtml || '<tr><td colspan="3" class="text-center">거래 기록이 없습니다.</td></tr>';
            return;
        }
        
        // 거래 기록이 있는 경우
        const history = await response.json();
        
        if (!history || history.length === 0) {
            document.getElementById('trade-history').innerHTML = '<tr><td colspan="3" class="text-center">거래 기록이 없습니다.</td></tr>';
            return;
        }
        
        // 최근 거래부터 표시
        const recentHistory = history.slice(-10).reverse();
        let historyHtml = '';
        
        for (const trade of recentHistory) {
            const type = trade.type;
            const time = trade.timestamp;
            let typeClass = type === 'buy' ? 'signal-buy' : 'signal-sell';
            
            historyHtml += `<tr>
                <td>${time}</td>
                <td class="${typeClass}">${type === 'buy' ? '매수' : '매도'}</td>
                <td>${formatKRW(trade.price)} x ${type === 'buy' ? formatKRW(trade.total) : trade.amount.toFixed(8)} BTC</td>
            </tr>`;
        }
        
        document.getElementById('trade-history').innerHTML = historyHtml;
    } catch (error) {
        console.error('거래 기록 로드 오류:', error);
        document.getElementById('trade-history').innerHTML = '<tr><td colspan="3" class="text-center">거래 기록을 불러올 수 없습니다.</td></tr>';
    }
}

// 차트 데이터 로드
async function loadChartData(days) {
    try {
        const dates = [];
        const today = new Date();
        
        // 차트에 표시할 날짜 배열 생성
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(today.getDate() - i);
            dates.push(date.toISOString().split('T')[0].replace(/-/g, ''));
        }
        
        // 날짜별 데이터 로드
        const signalData = {
            buy: Array(days).fill(0),
            sell: Array(days).fill(0),
            hold: Array(days).fill(0),
            confidence: Array(days).fill(0)
        };
        
        // 각 날짜에 대한 로그 파일 로드
        for (let i = 0; i < dates.length; i++) {
            try {
                const response = await fetch(`../logs/trading_log_${dates[i]}.json`);
                if (response.ok) {
                    const logs = await response.json();
                    
                    if (logs && logs.length > 0) {
                        // 해당 날짜의 마지막 데이터
                        const lastLog = logs[logs.length - 1];
                        
                        // 신호 카운트
                        const counts = lastLog.signal_counts || { buy: 0, sell: 0, hold: 0 };
                        signalData.buy[i] = counts.buy || 0;
                        signalData.sell[i] = counts.sell || 0;
                        signalData.hold[i] = counts.hold || 0;
                        
                        // 신뢰도
                        signalData.confidence[i] = lastLog.confidence || 0;
                    }
                }
            } catch (e) {
                console.log(`${dates[i]} 데이터 없음`);
            }
        }
        
        // 차트 업데이트
        updateSignalChart(dates.map(formatDateLabel), signalData);
    } catch (error) {
        console.error('차트 데이터 로드 오류:', error);
    }
}

// 차트 업데이트
function updateSignalChart(labels, data) {
    const ctx = document.getElementById('signals-chart').getContext('2d');
    
    // 기존 차트가 있으면 파괴
    if (signalsChart) {
        signalsChart.destroy();
    }
    
    // 신호 차트 생성
    signalsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    type: 'line',
                    label: '신뢰도',
                    data: data.confidence.map(v => v * 100),
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderWidth: 2,
                    tension: 0.2,
                    yAxisID: 'y1',
                    fill: true
                },
                {
                    type: 'bar',
                    label: '매수 신호',
                    data: data.buy,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                },
                {
                    type: 'bar',
                    label: '매도 신호',
                    data: data.sell,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                },
                {
                    type: 'bar',
                    label: '중립 신호',
                    data: data.hold,
                    backgroundColor: 'rgba(201, 203, 207, 0.6)',
                    borderColor: 'rgba(201, 203, 207, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: '신호 수'
                    }
                },
                y1: {
                    position: 'right',
                    title: {
                        display: true,
                        text: '신뢰도 (%)'
                    },
                    min: 0,
                    max: 100,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.datasetIndex === 0) {
                                label += context.raw.toFixed(1) + '%';
                            } else {
                                label += context.raw;
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
}

// 날짜 포맷팅
function formatDateLabel(dateStr) {
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    return `${month}/${day}`;
}

// 금액 포맷팅
function formatKRW(amount) {
    return new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW' }).format(amount);
}

// 신호 이모지 가져오기
function getSignalEmoji(signal) {
    if (signal === 'buy') return '🔼';
    if (signal === 'sell') return '🔽';
    return '➖';
}

// 신호 번역
function translateSignal(signal) {
    if (signal === 'buy') return '매수';
    if (signal === 'sell') return '매도';
    return '홀드';
}
