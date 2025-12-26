/**
 * Vanguard Data Journey Report
 * Interactive navigation and visualization
 */

document.addEventListener('DOMContentLoaded', function() {
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

        // Scroll to content start (below nav-bar)
        const navBar = document.querySelector('.nav-bar');
        const navBarHeight = navBar ? navBar.offsetHeight : 0;
        const progressBarHeight = 3; // progress-bar height
        const scrollTarget = navBarHeight + progressBarHeight;
        window.scrollTo({ top: scrollTarget, behavior: 'smooth' });
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
    // DEMO CHARTS
    // ============================================

    // Light Level Histogram Demo
    const lightChartCtx = document.getElementById('demoLightChart');
    if (lightChartCtx) {
        const gradient = lightChartCtx.getContext('2d').createLinearGradient(0, 0, 0, 250);
        gradient.addColorStop(0, 'rgba(33, 150, 243, 0.8)');
        gradient.addColorStop(1, 'rgba(33, 150, 243, 0.1)');

        new Chart(lightChartCtx, {
            type: 'bar',
            data: {
                labels: ['1780', '1790', '1800', '1810', '1820'],
                datasets: [{
                    label: 'Players',
                    data: [45, 120, 280, 350, 180],
                    backgroundColor: gradient,
                    borderColor: 'rgba(33, 150, 243, 1)',
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    annotation: {
                        annotations: {
                            meanLine: {
                                type: 'line',
                                xMin: 2.5,
                                xMax: 2.5,
                                borderColor: 'rgba(255, 99, 132, 0.9)',
                                borderWidth: 2,
                                borderDash: [6, 4],
                            },
                            medianLine: {
                                type: 'line',
                                xMin: 2.8,
                                xMax: 2.8,
                                borderColor: 'rgba(76, 175, 80, 0.9)',
                                borderWidth: 2,
                                borderDash: [5, 3],
                            },
                            q1Line: {
                                type: 'line',
                                xMin: 1.5,
                                xMax: 1.5,
                                borderColor: 'rgba(54, 162, 235, 0.7)',
                                borderWidth: 2,
                                borderDash: [4, 3],
                            },
                            q3Line: {
                                type: 'line',
                                xMin: 3.5,
                                xMax: 3.5,
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

    // Box Plot Demo
    const boxPlotDiv = document.getElementById('demoBoxPlot');
    if (boxPlotDiv) {
        // Sample data
        const titanData = Array.from({length: 50}, () => 1785 + Math.random() * 40);
        const hunterData = Array.from({length: 50}, () => 1790 + Math.random() * 35);
        const warlockData = Array.from({length: 50}, () => 1788 + Math.random() * 38);

        Plotly.newPlot(boxPlotDiv, [
            {
                y: titanData,
                name: 'Titan',
                type: 'box',
                marker: { color: '#ef5350' },
                boxmean: true,
            },
            {
                y: hunterData,
                name: 'Hunter',
                type: 'box',
                marker: { color: '#42a5f5' },
                boxmean: true,
            },
            {
                y: warlockData,
                name: 'Warlock',
                type: 'box',
                marker: { color: '#ffee58' },
                boxmean: true,
            }
        ], {
            title: { text: 'Light Level by Class', font: { size: 14, color: '#b0b0b0' } },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#888', size: 11 },
            margin: { l: 50, r: 20, t: 40, b: 40 },
            yaxis: {
                title: 'Light Level',
                gridcolor: 'rgba(255,255,255,0.05)',
            },
            showlegend: false,
        }, {
            responsive: true,
            displayModeBar: false,
        });
    }

    // Scatter Plot Demo
    const scatterPlotDiv = document.getElementById('demoScatterPlot');
    if (scatterPlotDiv) {
        // Sample data with correlation
        const n = 100;
        const lightLevels = Array.from({length: n}, () => 1780 + Math.random() * 40);
        const triumphScores = lightLevels.map(l => (l - 1780) * 1500 + 30000 + (Math.random() - 0.5) * 20000);

        // Trend line
        const minX = Math.min(...lightLevels);
        const maxX = Math.max(...lightLevels);
        const avgY = triumphScores.reduce((a, b) => a + b, 0) / n;
        const slope = 1200;
        const intercept = avgY - slope * ((minX + maxX) / 2);

        Plotly.newPlot(scatterPlotDiv, [
            {
                x: lightLevels,
                y: triumphScores,
                mode: 'markers',
                type: 'scatter',
                marker: {
                    color: 'rgba(255, 215, 0, 0.6)',
                    size: 8,
                },
                name: 'Players',
            },
            {
                x: [minX, maxX],
                y: [intercept + slope * minX, intercept + slope * maxX],
                mode: 'lines',
                type: 'scatter',
                line: { color: '#ff6b6b', width: 2, dash: 'dash' },
                name: 'Trend Line',
            }
        ], {
            title: { text: 'Light Level vs Triumph Score', font: { size: 14, color: '#b0b0b0' } },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#888', size: 11 },
            margin: { l: 60, r: 20, t: 40, b: 50 },
            xaxis: {
                title: 'Light Level',
                gridcolor: 'rgba(255,255,255,0.05)',
            },
            yaxis: {
                title: 'Triumph Score',
                gridcolor: 'rgba(255,255,255,0.05)',
            },
            showlegend: true,
            legend: { x: 0, y: 1, bgcolor: 'rgba(0,0,0,0)' },
        }, {
            responsive: true,
            displayModeBar: false,
        });
    }

    // Radar Chart Demo
    const radarChartCtx = document.getElementById('demoRadarChart');
    if (radarChartCtx) {
        new Chart(radarChartCtx, {
            type: 'radar',
            data: {
                labels: ['Light Level', 'Triumph Score', 'Play Time', 'PvP K/D', 'Raid Clears'],
                datasets: [{
                    label: 'Your Stats',
                    data: [85, 72, 60, 45, 55],
                    backgroundColor: 'rgba(255, 215, 0, 0.2)',
                    borderColor: 'rgba(255, 215, 0, 0.8)',
                    borderWidth: 2,
                    pointBackgroundColor: '#FFD700',
                    pointBorderColor: '#fff',
                    pointRadius: 4,
                }]
            },
            options: {
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
    // FILTER DEMO
    // ============================================

    const demoMinPlaytime = document.getElementById('demoMinPlaytime');
    const demoMinLight = document.getElementById('demoMinLight');
    const demoMinPlaytimeValue = document.getElementById('demoMinPlaytimeValue');
    const demoMinLightValue = document.getElementById('demoMinLightValue');
    const demoFilterCount = document.getElementById('demoFilterCount');

    // Sample player count logic
    const totalPlayers = 1250;

    function updateFilterDemo() {
        if (!demoMinPlaytime || !demoMinLight) return;

        const minPlaytime = parseInt(demoMinPlaytime.value);
        const minLight = parseInt(demoMinLight.value);

        demoMinPlaytimeValue.textContent = minPlaytime + 'h';
        demoMinLightValue.textContent = minLight;

        // Simulate filtering (exponential decay based on filters)
        const playtimeFactor = Math.max(0, 1 - minPlaytime / 600);
        const lightFactor = Math.max(0, 1 - (minLight - 1780) / 50);
        const filtered = Math.round(totalPlayers * playtimeFactor * lightFactor);

        demoFilterCount.textContent = filtered.toLocaleString();
    }

    if (demoMinPlaytime) {
        demoMinPlaytime.addEventListener('input', updateFilterDemo);
    }
    if (demoMinLight) {
        demoMinLight.addEventListener('input', updateFilterDemo);
    }

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
