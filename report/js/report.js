/**
 * Vanguard Data Journey Report
 * Interactive navigation and visualization
 */

// Prevent browser's automatic scroll restoration on refresh
if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
}

document.addEventListener('DOMContentLoaded', function() {
    // Reset scroll position on page load
    window.scrollTo(0, 0);

    // Initialize
    hljs.highlightAll();

    // ============================================
    // NAVIGATION SYSTEM
    // ============================================

    const sections = {
        hub: document.getElementById('hub'),
        sources: document.getElementById('sources'),
        collection: document.getElementById('collection'),
        storage: document.getElementById('storage'),
        processing: document.getElementById('processing'),
        visualization: document.getElementById('visualization'),
        ux: document.getElementById('ux'),
        conclusion: document.getElementById('conclusion')
    };

    const visitedSections = new Set();
    let currentSection = 'hub';

    // Navigation elements
    const floatingIndex = document.getElementById('floatingIndex');
    const hubBtn = document.getElementById('hubBtn');
    const breadcrumb = document.getElementById('breadcrumb');
    const progressDots = document.querySelectorAll('.progress-dot');
    const progressCount = document.querySelector('.progress-count');

    // Navigate to section
    function navigateTo(sectionId) {
        if (!sections[sectionId]) return;

        // Hide current section
        if (sections[currentSection]) {
            sections[currentSection].classList.remove('active');
        }

        // Show new section
        sections[sectionId].classList.add('active');
        currentSection = sectionId;

        // Mark as visited (except hub and conclusion)
        if (sectionId !== 'hub' && sectionId !== 'conclusion') {
            visitedSections.add(sectionId);
            updateProgress();
        }

        // Update UI
        updateFloatingIndex();
        updateBreadcrumb();
        updateHubBtn();
        updateHubNodes();

        // Scroll to appropriate position
        const navBar = document.querySelector('.nav-bar');
        const navBarHeight = navBar ? navBar.offsetHeight : 0;
        const progressBarHeight = 3;

        if (sectionId === 'hub') {
            // Hub: 네비게이션 바 바로 아래로 스크롤
            const scrollTarget = navBarHeight + progressBarHeight;
            window.scrollTo({ top: scrollTarget, behavior: 'smooth' });
        } else {
            // 다른 섹션: section-header(섹션 번호/제목)로 스크롤
            const sectionHeader = sections[sectionId].querySelector('.section-header');
            if (sectionHeader) {
                const headerTop = sectionHeader.getBoundingClientRect().top + window.scrollY;
                const scrollTarget = headerTop - navBarHeight - progressBarHeight - 30;
                window.scrollTo({ top: scrollTarget, behavior: 'smooth' });
            }
        }
    }

    // Update floating index
    function updateFloatingIndex() {
        floatingIndex.querySelectorAll('a').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.section === currentSection) {
                link.classList.add('active');
            }
        });
    }

    // Update breadcrumb
    function updateBreadcrumb() {
        const sectionNames = {
            hub: 'Data Journey',
            sources: 'Data Sources',
            collection: 'Collection',
            storage: 'Storage',
            processing: 'Processing',
            visualization: 'Visualization',
            ux: 'User Experience',
            conclusion: 'Conclusion'
        };

        if (currentSection === 'hub') {
            breadcrumb.innerHTML = '<span class="breadcrumb-item">Data Journey</span>';
        } else {
            breadcrumb.innerHTML = `
                <span class="breadcrumb-item" data-section="hub" style="cursor:pointer;">Hub</span>
                <span class="breadcrumb-item">${sectionNames[currentSection]}</span>
            `;
            breadcrumb.querySelector('[data-section="hub"]').addEventListener('click', () => navigateTo('hub'));
        }
    }

    // Update hub button visibility
    function updateHubBtn() {
        hubBtn.style.display = currentSection === 'hub' ? 'none' : 'block';
    }

    // Update hub nodes (mark visited)
    function updateHubNodes() {
        document.querySelectorAll('.hub-node').forEach(node => {
            const section = node.dataset.section;
            if (visitedSections.has(section)) {
                node.classList.add('visited');
            }
        });
    }

    // Update progress
    function updateProgress() {
        const mainSections = ['sources', 'collection', 'storage', 'processing', 'visualization', 'ux'];
        let count = 0;

        progressDots.forEach(dot => {
            if (visitedSections.has(dot.dataset.section)) {
                dot.classList.add('visited');
                count++;
            }
        });

        if (progressCount) {
            progressCount.textContent = `${count} / 6`;
        }
    }

    // Event: Hub nodes
    document.querySelectorAll('.hub-node').forEach(node => {
        node.addEventListener('click', () => {
            navigateTo(node.dataset.section);
        });
    });

    // Event: Floating index
    floatingIndex.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo(link.dataset.section);
        });
    });

    // Event: Hub button
    hubBtn.addEventListener('click', () => navigateTo('hub'));

    // Event: Back to hub buttons
    document.querySelectorAll('.back-to-hub').forEach(btn => {
        btn.addEventListener('click', () => navigateTo(btn.dataset.section));
    });

    // Event: Navigation buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => navigateTo(btn.dataset.section));
    });

    // Event: Quick links
    document.querySelectorAll('.quick-link').forEach(link => {
        link.addEventListener('click', () => navigateTo(link.dataset.section));
    });

    // ============================================
    // PROGRESS BAR
    // ============================================

    const progressBar = document.getElementById('progressBar');

    function updateProgressBar() {
        const scrollTop = window.scrollY;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
        progressBar.style.width = scrollPercent + '%';
    }

    window.addEventListener('scroll', updateProgressBar);

    // ============================================
    // HUB CONNECTIONS (SVG Lines)
    // ============================================

    function drawHubConnections() {
        const svg = document.querySelector('.hub-connections');
        const linesGroup = svg.querySelector('.connection-lines');
        const center = { x: 200, y: 200 };

        // Node positions matching CSS layout (400x400 container)
        // angle="0": top center, angle="60": top-right, angle="120": bottom-right
        // angle="180": bottom center, angle="240": bottom-left, angle="300": top-left
        const nodePositions = [
            { x: 200, y: 50 },   // angle="0" - Data Sources (top center)
            { x: 350, y: 100 },  // angle="60" - Collection (top-right)
            { x: 350, y: 300 },  // angle="120" - Storage (bottom-right)
            { x: 200, y: 350 },  // angle="180" - Processing (bottom center)
            { x: 50, y: 300 },   // angle="240" - Visualization (bottom-left)
            { x: 50, y: 100 }    // angle="300" - UX (top-left)
        ];

        linesGroup.innerHTML = '';

        nodePositions.forEach(pos => {
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', center.x);
            line.setAttribute('y1', center.y);
            line.setAttribute('x2', pos.x);
            line.setAttribute('y2', pos.y);
            linesGroup.appendChild(line);
        });
    }

    drawHubConnections();

    // ============================================
    // MODEL TABS
    // ============================================

    document.querySelectorAll('.model-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const model = tab.dataset.model;

            // Update tabs
            document.querySelectorAll('.model-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update panels
            document.querySelectorAll('.model-panel').forEach(p => p.classList.remove('active'));
            document.querySelector(`.model-panel[data-model="${model}"]`).classList.add('active');
        });
    });

    // ============================================
    // CODE TOGGLE
    // ============================================

    document.querySelectorAll('.toggle-code-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const target = document.getElementById(btn.dataset.target);
            if (target) {
                target.classList.toggle('open');
                btn.textContent = target.classList.contains('open') ? 'Hide Code' : 'View Code';
            }
        });
    });

    // ============================================
    // ENDPOINT TREE TOGGLE
    // ============================================

    document.querySelectorAll('.category-header').forEach(header => {
        header.addEventListener('click', () => {
            const expanded = header.dataset.expanded === 'true';
            header.dataset.expanded = (!expanded).toString();

            const items = header.nextElementSibling;
            if (items) {
                items.style.display = expanded ? 'none' : 'block';
            }
        });
    });

    // ============================================
    // DEMO CHARTS (API 연동 + 폴백 데이터)
    // ============================================

    // 차트 렌더링 헬퍼 함수
    function renderLightChart(ctx, labels, values, stats) {
        const findIndex = (val) => {
            for (let i = 0; i < labels.length; i++) {
                const bucketStart = parseInt(labels[i]);
                if (val >= bucketStart && val < bucketStart + 10) return i;
            }
            return labels.length / 2;
        };

        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 250);
        gradient.addColorStop(0, 'rgba(33, 150, 243, 0.8)');
        gradient.addColorStop(1, 'rgba(33, 150, 243, 0.1)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Characters',
                    data: values,
                    fill: true,
                    tension: 0.4,
                    backgroundColor: gradient,
                    borderColor: 'rgba(33, 150, 243, 1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointBackgroundColor: 'rgba(33, 150, 243, 1)',
                }]
            },
            options: {
                animation: false,
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    annotation: {
                        annotations: {
                            meanLine: {
                                type: 'line',
                                xMin: findIndex(stats.avg),
                                xMax: findIndex(stats.avg),
                                borderColor: 'rgba(255, 99, 132, 0.9)',
                                borderWidth: 2,
                                borderDash: [6, 4],
                            },
                            medianLine: {
                                type: 'line',
                                xMin: findIndex(stats.median),
                                xMax: findIndex(stats.median),
                                borderColor: 'rgba(76, 175, 80, 0.9)',
                                borderWidth: 2,
                                borderDash: [5, 3],
                            },
                            q1Line: {
                                type: 'line',
                                xMin: findIndex(stats.q1),
                                xMax: findIndex(stats.q1),
                                borderColor: 'rgba(54, 162, 235, 0.7)',
                                borderWidth: 2,
                                borderDash: [4, 3],
                            },
                            q3Line: {
                                type: 'line',
                                xMin: findIndex(stats.q3),
                                xMax: findIndex(stats.q3),
                                borderColor: 'rgba(54, 162, 235, 0.7)',
                                borderWidth: 2,
                                borderDash: [4, 3],
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#888' }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#888' },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    function renderBoxPlot(div, titanData, hunterData, warlockData) {
        Plotly.newPlot(div, [
            { y: titanData, name: 'Titan', type: 'box', marker: { color: '#ef5350' }, boxmean: true },
            { y: hunterData, name: 'Hunter', type: 'box', marker: { color: '#42a5f5' }, boxmean: true },
            { y: warlockData, name: 'Warlock', type: 'box', marker: { color: '#ffee58' }, boxmean: true }
        ], {
            title: { text: 'Light Level by Class', font: { size: 14, color: '#b0b0b0' } },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#888', size: 11 },
            margin: { l: 50, r: 20, t: 40, b: 40 },
            yaxis: { title: 'Light Level', gridcolor: 'rgba(255,255,255,0.05)' },
            showlegend: false,
            transition: { duration: 0 },
        }, { responsive: true, displayModeBar: false });
    }

    function renderScatterPlot(div, lightLevels, triumphScores, slope, intercept) {
        const minX = Math.min(...lightLevels);
        const maxX = Math.max(...lightLevels);

        Plotly.newPlot(div, [
            {
                x: lightLevels, y: triumphScores,
                mode: 'markers', type: 'scatter',
                marker: { color: 'rgba(255, 215, 0, 0.6)', size: 8 },
                name: 'Players',
            },
            {
                x: [minX, maxX],
                y: [slope * minX + intercept, slope * maxX + intercept],
                mode: 'lines', type: 'scatter',
                line: { color: '#ff6b6b', width: 2, dash: 'dash' },
                name: 'Trend Line',
            }
        ], {
            title: { text: 'Light Level vs Triumph Score', font: { size: 14, color: '#b0b0b0' } },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#888', size: 11 },
            margin: { l: 60, r: 120, t: 40, b: 50 },
            xaxis: { title: 'Light Level', gridcolor: 'rgba(255,255,255,0.05)' },
            yaxis: { title: 'Triumph Score', gridcolor: 'rgba(255,255,255,0.05)' },
            showlegend: true,
            legend: { x: 1.02, y: 1, xanchor: 'left', yanchor: 'top', bgcolor: 'rgba(0,0,0,0)' },
            transition: { duration: 0 },
        }, { responsive: true, displayModeBar: false });
    }

    // 폴백 데이터 (API 실패 시 사용)
    const fallbackData = {
        light: {
            distribution: { '1780': 45, '1790': 120, '1800': 280, '1810': 350, '1820': 180 },
            stats: { avg: 1805, median: 1808, q1: 1795, q3: 1815 }
        },
        boxplot: {
            titan: Array.from({length: 50}, () => 1785 + Math.random() * 40),
            hunter: Array.from({length: 50}, () => 1790 + Math.random() * 35),
            warlock: Array.from({length: 50}, () => 1788 + Math.random() * 38)
        },
        scatter: {
            x: Array.from({length: 100}, () => 1780 + Math.random() * 40),
            slope: 1200,
            intercept: -2100000
        }
    };
    fallbackData.scatter.y = fallbackData.scatter.x.map(l =>
        (l - 1780) * 1500 + 30000 + (Math.random() - 0.5) * 20000
    );

    // Light Level Histogram Demo
    const lightChartCtx = document.getElementById('demoLightChart');
    if (lightChartCtx) {
        Promise.all([
            fetch('/api/statistics/distribution/').then(res => res.json()),
            fetch('/api/statistics/descriptive/').then(res => res.json())
        ])
            .then(([distData, statsData]) => {
                const dist = distData.light_level_distribution;
                const stats = {
                    avg: statsData.light_level.mean,
                    median: statsData.light_level.median,
                    q1: statsData.light_level.q1,
                    q3: statsData.light_level.q3
                };
                renderLightChart(lightChartCtx, Object.keys(dist), Object.values(dist), stats);
            })
            .catch(() => {
                // API 실패 시 폴백 데이터 사용
                const fb = fallbackData.light;
                renderLightChart(lightChartCtx, Object.keys(fb.distribution), Object.values(fb.distribution), fb.stats);
            });
    }

    // Box Plot Demo
    const boxPlotDiv = document.getElementById('demoBoxPlot');
    if (boxPlotDiv) {
        fetch('/api/statistics/class-comparison/')
            .then(res => res.json())
            .then(data => {
                const bp = data.visualization_data.data;
                renderBoxPlot(boxPlotDiv, bp.titan, bp.hunter, bp.warlock);
            })
            .catch(() => {
                // API 실패 시 폴백 데이터 사용
                const fb = fallbackData.boxplot;
                renderBoxPlot(boxPlotDiv, fb.titan, fb.hunter, fb.warlock);
            });
    }

    // Scatter Plot Demo
    const scatterPlotDiv = document.getElementById('demoScatterPlot');
    if (scatterPlotDiv) {
        fetch('/api/statistics/correlation/')
            .then(res => res.json())
            .then(data => {
                const corr = data.correlation_analysis;
                renderScatterPlot(scatterPlotDiv, corr.scatter_data.x, corr.scatter_data.y,
                    corr.regression.slope, corr.regression.intercept);
            })
            .catch(() => {
                // API 실패 시 폴백 데이터 사용
                const fb = fallbackData.scatter;
                renderScatterPlot(scatterPlotDiv, fb.x, fb.y, fb.slope, fb.intercept);
            });
    }

    // Radar Chart Demo - 백엔드 지원 5축 (중간값 더미 데이터)
    const radarChartCtx = document.getElementById('demoRadarChart');
    if (radarChartCtx) {
        new Chart(radarChartCtx, {
            type: 'radar',
            data: {
                // 백엔드 get_radar_chart_data() 함수와 동일한 축
                labels: ['Light Level', 'Triumph', 'Play Time', 'Characters', 'Versatility'],
                datasets: [{
                    label: 'Sample Player',
                    // 일반적인 플레이어 프로필을 대표하는 중간값 더미 데이터
                    // Light Level: 65 (상위 35%), Triumph: 55 (중간), Play Time: 48 (평균 하회)
                    // Characters: 66 (2개 보유), Versatility: 66 (2종 클래스)
                    data: [65, 55, 48, 66, 66],
                    backgroundColor: 'rgba(255, 215, 0, 0.2)',
                    borderColor: 'rgba(255, 215, 0, 0.8)',
                    borderWidth: 2,
                    pointBackgroundColor: '#FFD700',
                    pointBorderColor: '#fff',
                    pointRadius: 4,
                }]
            },
            options: {
                animation: false,
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            color: '#888',
                            backdropColor: 'transparent',
                            font: { size: 9 },
                        },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                        pointLabels: {
                            color: '#b0b0b0',
                            font: { size: 10 },
                        },
                    },
                },
                plugins: {
                    legend: { display: false },
                },
            },
        });
    }

    // ============================================
    // FILTER DEMO (API 연동)
    // ============================================

    const demoMinPlaytime = document.getElementById('demoMinPlaytime');
    const demoMinLight = document.getElementById('demoMinLight');
    const demoMinPlaytimeValue = document.getElementById('demoMinPlaytimeValue');
    const demoMinLightValue = document.getElementById('demoMinLightValue');
    const demoFilterCount = document.getElementById('demoFilterCount');

    // API 기본 URL (동일 도메인이면 빈 문자열, 다른 도메인이면 전체 URL)
    const API_BASE_URL = '';

    // Debounce 유틸리티
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // 폴백용 변수 (API 실패 시 사용)
    let fallbackTotalPlayers = 1250;
    let useApiFallback = false;

    // 폴백 로직 (기존 exponential decay 방식)
    function updateFilterDemoFallback() {
        if (!demoMinPlaytime || !demoMinLight) return;

        const minPlaytime = parseInt(demoMinPlaytime.value);
        const minLight = parseInt(demoMinLight.value);

        demoMinPlaytimeValue.textContent = minPlaytime + 'h';
        demoMinLightValue.textContent = minLight;

        const playtimeFactor = Math.max(0, 1 - minPlaytime / 600);
        const lightFactor = Math.max(0, 1 - (minLight - 1780) / 50);
        const filtered = Math.round(fallbackTotalPlayers * playtimeFactor * lightFactor);

        demoFilterCount.textContent = filtered.toLocaleString();
    }

    // API 호출 로직
    async function fetchFilteredCount(minPlaytime, minLight) {
        const url = `${API_BASE_URL}/api/statistics/filtered-count/?min_playtime=${minPlaytime}&min_light=${minLight}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('API request failed');
        return response.json();
    }

    // 필터 업데이트 (debounced)
    const updateFilterDemo = debounce(async () => {
        if (!demoMinPlaytime || !demoMinLight) return;

        const minPlaytime = parseInt(demoMinPlaytime.value);
        const minLight = parseInt(demoMinLight.value);

        // 즉시 UI 업데이트
        demoMinPlaytimeValue.textContent = minPlaytime + 'h';
        demoMinLightValue.textContent = minLight;

        if (useApiFallback) {
            // API 사용 불가 시 폴백 로직
            updateFilterDemoFallback();
            return;
        }

        try {
            const result = await fetchFilteredCount(minPlaytime, minLight);
            demoFilterCount.textContent = result.filtered_count.toLocaleString();
        } catch (error) {
            console.warn('Filter API call failed, using fallback:', error);
            updateFilterDemoFallback();
        }
    }, 300);

    // 필터 초기화 (API에서 통계 범위 가져오기)
    async function initFilterDemo() {
        if (!demoMinPlaytime || !demoMinLight) return;

        try {
            // 기술 통계 API에서 범위 정보 가져오기
            const statsResponse = await fetch(`${API_BASE_URL}/api/statistics/descriptive/`);
            if (!statsResponse.ok) throw new Error('Failed to fetch statistics');

            const stats = await statsResponse.json();

            // 라이트 레벨 슬라이더 범위 설정
            const lightMin = stats.light_level.min || 1780;
            const lightMax = stats.light_level.max || 1820;
            demoMinLight.min = lightMin;
            demoMinLight.max = lightMax;
            demoMinLight.value = lightMin;
            demoMinLightValue.textContent = lightMin;

            // 플레이 타임 슬라이더 범위 설정 (Q3의 2배 또는 최대 1000시간)
            const playtimeMax = Math.min(
                Math.round((stats.play_time_hours.q3 || 250) * 2),
                1000
            );
            demoMinPlaytime.max = playtimeMax;
            demoMinPlaytime.value = 0;
            demoMinPlaytimeValue.textContent = '0h';

            // 총 플레이어 수 저장 (폴백용)
            fallbackTotalPlayers = stats.metadata.total_players || 1250;

            // 초기 카운트 로드
            const initialResult = await fetchFilteredCount(0, lightMin);
            demoFilterCount.textContent = initialResult.filtered_count.toLocaleString();

        } catch (error) {
            console.warn('Filter initialization failed, using fallback mode:', error);
            useApiFallback = true;
            // 기존 하드코딩된 범위 유지
            updateFilterDemoFallback();
        }
    }

    // 이벤트 리스너 등록
    if (demoMinPlaytime) {
        demoMinPlaytime.addEventListener('input', updateFilterDemo);
    }
    if (demoMinLight) {
        demoMinLight.addEventListener('input', updateFilterDemo);
    }

    // 필터 초기화 실행
    initFilterDemo();

    // ============================================
    // CODE COPY BUTTON
    // ============================================

    document.querySelectorAll('.code-copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const codeBlock = btn.closest('.code-block-container').querySelector('code');
            if (codeBlock) {
                navigator.clipboard.writeText(codeBlock.textContent).then(() => {
                    btn.textContent = 'Copied!';
                    setTimeout(() => {
                        btn.textContent = 'Copy';
                    }, 2000);
                });
            }
        });
    });

    // ============================================
    // INTERSECTION OBSERVER FOR ANIMATIONS
    // ============================================

    const animationObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.content-block, .oauth-flow, .sync-pipeline, .processing-pipeline, .two-column, .erd-container').forEach(el => {
        animationObserver.observe(el);
    });

    // ============================================
    // INITIAL STATE
    // ============================================

    navigateTo('hub');
    updateProgressBar();
});
