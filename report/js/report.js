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
        if (!floatingIndex) return;
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
    if (floatingIndex) {
        floatingIndex.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                navigateTo(link.dataset.section);
            });
        });
    }

    // Event: Hub button
    if (hubBtn) {
        hubBtn.addEventListener('click', () => navigateTo('hub'));
    }

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
        if (!svg) return; // Guard clause
        const linesGroup = svg.querySelector('.connection-lines');
        if (!linesGroup) return; // Guard clause
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

    // ============================================
    // INTERACTIVE FILTER + DYNAMIC RADAR CHART
    // ============================================

    // API 기본 URL (동일 도메인이면 빈 문자열)
    const API_BASE_URL = '';

    // Filter input elements
    const filterInputs = {
        minPlaytime: document.getElementById('demoMinPlaytime'),
        maxPlaytime: document.getElementById('demoMaxPlaytime'),
        minLight: document.getElementById('demoMinLight'),
        maxLight: document.getElementById('demoMaxLight'),
        minTriumph: document.getElementById('demoMinTriumph'),
        maxTriumph: document.getElementById('demoMaxTriumph'),
    };
    const demoFilterCount = document.getElementById('demoFilterCount');
    const radarChartCtx = document.getElementById('demoRadarChart');

    // Radar chart instance (will be created dynamically)
    let radarChart = null;

    // Debounce utility
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // Create or update radar chart
    function updateRadarChart(percentiles) {
        if (!radarChartCtx) return;

        const data = percentiles ? [
            percentiles.light_level,
            percentiles.triumph,
            percentiles.play_time,
            percentiles.characters,
            percentiles.versatility
        ] : [50, 50, 50, 50, 50]; // Default center values

        if (radarChart) {
            // Update existing chart
            radarChart.data.datasets[0].data = data;
            radarChart.update('none');
        } else {
            // Create new chart
            radarChart = new Chart(radarChartCtx, {
                type: 'radar',
                data: {
                    labels: ['Light Level', 'Triumph', 'Play Time', 'Characters', 'Versatility'],
                    datasets: [{
                        label: 'Filtered Average',
                        data: data,
                        backgroundColor: 'rgba(255, 215, 0, 0.2)',
                        borderColor: 'rgba(255, 215, 0, 0.8)',
                        borderWidth: 2,
                        pointBackgroundColor: '#FFD700',
                        pointBorderColor: '#fff',
                        pointRadius: 4,
                    }]
                },
                options: {
                    animation: { duration: 300 },
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
    }

    // Get filter values from inputs
    function getFilterValues() {
        const getValue = (input) => {
            if (!input || input.value === '') return null;
            const val = parseFloat(input.value);
            return isNaN(val) ? null : val;
        };

        return {
            minPlaytime: getValue(filterInputs.minPlaytime),
            maxPlaytime: getValue(filterInputs.maxPlaytime),
            minLight: getValue(filterInputs.minLight),
            maxLight: getValue(filterInputs.maxLight),
            minTriumph: getValue(filterInputs.minTriumph),
            maxTriumph: getValue(filterInputs.maxTriumph),
        };
    }

    // Build API query string
    function buildQueryString(filters) {
        const params = new URLSearchParams();
        if (filters.minPlaytime !== null) params.append('min_playtime', filters.minPlaytime);
        if (filters.maxPlaytime !== null) params.append('max_playtime', filters.maxPlaytime);
        if (filters.minLight !== null) params.append('min_light', filters.minLight);
        if (filters.maxLight !== null) params.append('max_light', filters.maxLight);
        if (filters.minTriumph !== null) params.append('min_triumph', filters.minTriumph);
        if (filters.maxTriumph !== null) params.append('max_triumph', filters.maxTriumph);
        return params.toString();
    }

    // Fetch filtered statistics from API
    async function fetchFilteredStats(filters) {
        const queryString = buildQueryString(filters);
        const url = `${API_BASE_URL}/api/statistics/filtered-count/${queryString ? '?' + queryString : ''}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('API request failed');
        return response.json();
    }

    // Fallback data for filter demo when API is unavailable
    const filterFallbackData = {
        totalPlayers: 1250,
        percentiles: { light_level: 50, triumph: 50, play_time: 50, characters: 66, versatility: 66 }
    };

    // Update filter demo (debounced)
    const updateFilterDemo = debounce(async () => {
        if (!demoFilterCount) return;

        const filters = getFilterValues();

        try {
            const result = await fetchFilteredStats(filters);

            // Update count
            demoFilterCount.textContent = result.filtered_count.toLocaleString();

            // Update radar chart with percentiles
            if (result.percentiles) {
                updateRadarChart(result.percentiles);
            } else {
                // No matching players - show empty/center chart
                updateRadarChart(null);
            }
        } catch (error) {
            console.warn('Filter API call failed:', error);
            // Use fallback
            demoFilterCount.textContent = filterFallbackData.totalPlayers.toLocaleString();
            updateRadarChart(filterFallbackData.percentiles);
        }
    }, 300);

    // Initialize filter demo
    async function initFilterDemo() {
        try {
            // Check if filter elements exist
            const hasFilterInputs = Object.values(filterInputs).some(input => input !== null);
            if (!hasFilterInputs && !demoFilterCount) return;

            // Initialize radar chart with default data
            updateRadarChart(filterFallbackData.percentiles);

            // Load initial data
            try {
                const result = await fetchFilteredStats({});
                if (demoFilterCount) {
                    demoFilterCount.textContent = result.filtered_count.toLocaleString();
                }
                if (result.percentiles) {
                    updateRadarChart(result.percentiles);
                }
            } catch (error) {
                console.warn('Initial filter load failed:', error);
                if (demoFilterCount) {
                    demoFilterCount.textContent = filterFallbackData.totalPlayers.toLocaleString();
                }
            }

            // Add event listeners to all filter inputs
            Object.values(filterInputs).forEach(input => {
                if (input) {
                    input.addEventListener('input', updateFilterDemo);
                }
            });
        } catch (error) {
            console.error('Filter demo initialization error:', error);
        }
    }

    // Initialize filter demo (non-blocking)
    initFilterDemo().catch(err => console.error('initFilterDemo error:', err));

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
