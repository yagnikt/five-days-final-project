// AeroPlan AI - Core Interactive Logic & State Orchestration

const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL !== undefined) ? import.meta.env.VITE_API_BASE_URL : 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
  // 1. Session Setup & Persistent State
  let userId = localStorage.getItem('aeroplan_user_id');
  if (!userId) {
    userId = 'user_' + Math.random().toString(36).substring(2, 11);
    localStorage.setItem('aeroplan_user_id', userId);
  }
  let sessionId = localStorage.getItem('aeroplan_session_id');
  if (!sessionId) {
    sessionId = 'session_' + Math.random().toString(36).substring(2, 11);
    localStorage.setItem('aeroplan_session_id', sessionId);
  }

  console.log(`Initialized AeroPlan Session for Client: ${userId} (${sessionId})`);

  // 2. Navigation Tab Control
  const navPlannerBtn = document.getElementById('nav-btn-planner');
  const navAdminBtn = document.getElementById('nav-btn-admin');
  const viewPlanner = document.getElementById('view-planner');
  const viewAdmin = document.getElementById('view-admin');

  function switchTab(target) {
    if (target === 'planner') {
      navPlannerBtn.classList.add('active');
      navAdminBtn.classList.remove('active');
      viewPlanner.classList.add('active');
      viewAdmin.classList.remove('active');
    } else {
      navPlannerBtn.classList.remove('active');
      navAdminBtn.classList.add('active');
      viewPlanner.classList.remove('active');
      viewAdmin.classList.add('active');
      fetchPendingApprovals(); // auto-refresh queue when admin logs in
    }
  }

  navPlannerBtn.addEventListener('click', () => switchTab('planner'));
  navAdminBtn.addEventListener('click', () => switchTab('admin'));

  // 3. Form Submission & Generation Polling
  const form = document.getElementById('itinerary-form');
  const promptInput = document.getElementById('prompt');
  const submitBtn = document.getElementById('btn-submit-request');
  const progressSection = document.getElementById('progress-section');
  const terminalSection = document.getElementById('terminal-section');
  const terminalLogs = document.getElementById('terminal-logs');
  const terminalStatus = document.getElementById('terminal-status');
  const progressStatusText = document.getElementById('progress-status-text');
  
  const stepInit = document.getElementById('step-init');
  const stepSearch = document.getElementById('step-search');
  const stepEval = document.getElementById('step-eval');
  const stepReview = document.getElementById('step-review');

  const itineraryOutputSection = document.getElementById('itinerary-output-section');
  const itineraryDest = document.getElementById('itinerary-dest');
  const itinerarySummary = document.getElementById('itinerary-summary');
  const itineraryCost = document.getElementById('itinerary-cost');
  const itineraryDetailsContainer = document.getElementById('itinerary-details-container');

  let pollIntervalId = null;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = promptInput.value.trim();
    if (!query) return;

    // Reset UI state
    submitBtn.disabled = true;
    submitBtn.textContent = 'Orchestrating...';
    progressSection.classList.remove('hidden');
    terminalSection.classList.remove('hidden');
    itineraryOutputSection.classList.add('hidden');
    terminalLogs.innerHTML = '<div class="terminal-log-line">Sending request to AeroPlan AI orchestrator...</div>';
    terminalStatus.textContent = 'processing';
    terminalStatus.className = 'terminal-badge';
    
    resetProgressStepper();

    try {
      const response = await fetch(`${API_BASE_URL}/api/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, user_id: userId, session_id: sessionId })
      });

      if (!response.ok) {
        throw new Error(`Server returned error: ${response.statusText}`);
      }

      const data = await response.json();
      const requestId = data.request_id;
      
      appendTerminalLog(`Request registered successfully. Request ID: ${requestId}`);
      appendTerminalLog('Spawning generation background thread...');

      // Start Polling
      if (pollIntervalId) clearInterval(pollIntervalId);
      pollIntervalId = setInterval(() => pollRequestStatus(requestId), 2000);

    } catch (err) {
      appendTerminalLog(`❌ Orchestration Initiation Failed: ${err.message}`);
      terminalStatus.textContent = 'failed';
      terminalStatus.className = 'terminal-badge error';
      submitBtn.disabled = false;
      submitBtn.textContent = 'Generate Itinerary';
    }
  });

  function resetProgressStepper() {
    [stepInit, stepSearch, stepEval, stepReview].forEach(step => {
      step.className = 'step';
    });
    // Reset step line connectors
    const stepLines = document.querySelectorAll('.step-line');
    stepLines.forEach(line => line.className = 'step-line');
    progressStatusText.textContent = 'Initializing agent environment...';
  }

  function appendTerminalLog(message) {
    const line = document.createElement('div');
    line.className = 'terminal-log-line';
    line.textContent = message;
    terminalLogs.appendChild(line);
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
  }

  async function pollRequestStatus(requestId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/status/${requestId}`);
      if (!response.ok) return;

      const reqData = await response.json();
      
      // Update console logs stream
      terminalLogs.innerHTML = '';
      if (reqData.logs && reqData.logs.length > 0) {
        reqData.logs.forEach(logLine => {
          const line = document.createElement('div');
          line.className = 'terminal-log-line';
          line.textContent = logLine;
          terminalLogs.appendChild(line);
        });
        terminalLogs.scrollTop = terminalLogs.scrollHeight;
      }

      const status = reqData.status;
      const logsText = reqData.logs ? reqData.logs.join('\n') : '';

      // Update progress bar UI states intelligently
      updateProgressStepper(status, logsText);

      if (status === 'approved') {
        clearInterval(pollIntervalId);
        terminalStatus.textContent = 'approved';
        terminalStatus.className = 'terminal-badge success';
        appendTerminalLog('✅ Itinerary proposal APPROVED by admin! Displaying finalized result.');
        
        // Hide loaders, show result
        setTimeout(() => {
          progressSection.classList.add('hidden');
          terminalSection.classList.add('hidden');
          renderFinalItinerary(reqData.itinerary);
          submitBtn.disabled = false;
          submitBtn.textContent = 'Generate Itinerary';
        }, 1500);

      } else if (status === 'rejected') {
        clearInterval(pollIntervalId);
        terminalStatus.textContent = 'rejected';
        terminalStatus.className = 'terminal-badge';
        appendTerminalLog('❌ Proposal rejected by Administrator.');
        progressStatusText.textContent = 'Proposal rejected. Please try modifying your constraints.';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Generate Itinerary';

      } else if (status === 'failed') {
        clearInterval(pollIntervalId);
        terminalStatus.textContent = 'failed';
        terminalStatus.className = 'terminal-badge error';
        appendTerminalLog('❌ Gen-loop pipeline execution failed.');
        progressStatusText.textContent = 'Pipeline execution failed. Please verify preferences and retry.';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Generate Itinerary';
      }

    } catch (err) {
      console.error('Error polling request status:', err);
    }
  }

  function updateProgressStepper(status, logsText) {
    const stepLines = document.querySelectorAll('.step-line');

    if (status === 'processing') {
      if (logsText.includes('Evaluating proposal') || logsText.includes('Running Evaluator')) {
        // Step 3 active
        stepInit.className = 'step completed';
        stepLines[0].className = 'step-line completed';
        stepSearch.className = 'step completed';
        stepLines[1].className = 'step-line completed';
        stepEval.className = 'step active';
        stepLines[2].className = 'step-line';
        stepReview.className = 'step';
        progressStatusText.textContent = 'Running LLM-as-a-judge QA metrics validation...';
      } else if (logsText.includes('Querying Google Search') || logsText.includes('Invoking google_search') || logsText.includes('Search results found')) {
        // Step 2 active
        stepInit.className = 'step completed';
        stepLines[0].className = 'step-line completed';
        stepSearch.className = 'step active';
        stepLines[1].className = 'step-line';
        stepEval.className = 'step';
        stepLines[2].className = 'step-line';
        stepReview.className = 'step';
        progressStatusText.textContent = 'Google Search grounding active: fetching real-time flights & hotel options...';
      } else {
        // Step 1 active
        stepInit.className = 'step active';
        stepLines[0].className = 'step-line';
        stepSearch.className = 'step';
        stepLines[1].className = 'step-line';
        stepEval.className = 'step';
        stepLines[2].className = 'step-line';
        stepReview.className = 'step';
        progressStatusText.textContent = 'Initializing premium travel planner agent...';
      }
    } else if (status === 'pending_approval') {
      // Step 4 active
      stepInit.className = 'step completed';
      stepLines[0].className = 'step-line completed';
      stepSearch.className = 'step completed';
      stepLines[1].className = 'step-line completed';
      stepEval.className = 'step completed';
      stepLines[2].className = 'step-line completed';
      stepReview.className = 'step active';
      progressStatusText.textContent = 'Awaiting Admin authorization on HITL gateway...';
    } else if (status === 'approved') {
      stepInit.className = 'step completed';
      stepLines[0].className = 'step-line completed';
      stepSearch.className = 'step completed';
      stepLines[1].className = 'step-line completed';
      stepEval.className = 'step completed';
      stepLines[2].className = 'step-line completed';
      stepReview.className = 'step completed';
      progressStatusText.textContent = 'Itinerary ready and verified!';
    }
  }

  function renderFinalItinerary(itinerary) {
    if (!itinerary) return;

    itineraryOutputSection.classList.remove('hidden');
    itineraryDest.textContent = itinerary.destination || 'Custom Weekend Trip';
    itinerarySummary.textContent = itinerary.summary || '';
    itineraryCost.textContent = `$${(itinerary.total_estimated_cost || 0).toFixed(2)}`;

    let html = '';

    // Render Fallback pathways if requested
    if (itinerary.fallback_requested) {
      html += `
        <div class="eval-feedback" style="border-left-color: var(--color-accent); background: rgba(244, 63, 94, 0.05); margin-top: 2rem;">
          <h3 style="color: var(--color-accent); margin-bottom: 0.5rem;">⚠️ Generation Notice</h3>
          <p>${itinerary.fallback_message || 'Could not satisfying constraints. Please expand your budget or relax constraints.'}</p>
        </div>
      `;
    }

    // Flights
    if (itinerary.flights && itinerary.flights.length > 0) {
      html += `
        <div class="section-title">✈️ Grounded Flights</div>
        <div class="flight-card">
          <div class="flight-grid">
            ${itinerary.flights.map(f => `
              <div class="flight-leg">
                <div class="flight-num">${f.airline} (${f.flight_number})</div>
                <div style="margin: 0.5rem 0 0.25rem 0;"><strong>Route:</strong> ${f.departure_airport} ➔ ${f.arrival_airport}</div>
                <div style="font-size: 0.9rem; color: var(--text-secondary);"><strong>Dept:</strong> ${f.departure_time}</div>
                <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem;"><strong>Arr:</strong> ${f.arrival_time}</div>
                <div><strong>Est. Price:</strong> $${f.price ? f.price.toFixed(2) : '0.00'}</div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    // Hotel
    if (itinerary.accommodation) {
      const acc = itinerary.accommodation;
      html += `
        <div class="section-title">🏨 Premium Accommodation</div>
        <div class="hotel-card">
          <div class="hotel-header">
            <h3 style="font-family: var(--font-family-display); font-size: 1.25rem; font-weight: 700;">${acc.name}</h3>
            ${acc.rating ? `<span class="hotel-rating">★ ${acc.rating}</span>` : ''}
          </div>
          ${acc.address ? `<p style="color: var(--text-secondary); margin-bottom: 0.5rem; font-size: 0.95rem;">📍 ${acc.address}</p>` : ''}
          <p><strong>Est. Cost per Night:</strong> $${acc.price_per_night ? acc.price_per_night.toFixed(2) : '0.00'}</p>
          ${acc.booking_link ? `<a href="${acc.booking_link}" target="_blank" class="booking-btn">Booking Reference ➔</a>` : ''}
        </div>
      `;
    }

    // Days Schedule
    if (itinerary.itinerary_days && itinerary.itinerary_days.length > 0) {
      html += `<div class="section-title">🗓️ Tailored Itinerary Days</div>`;
      itinerary.itinerary_days.forEach(d => {
        html += `
          <div class="day-card">
            <div class="day-title">Day ${d.day_number}: ${d.date}</div>
            <div class="activity-timeline">
              ${d.activities.map(act => `
                <div class="activity-item">
                  <div class="activity-dot"></div>
                  <div class="activity-time">${act.time}</div>
                  <div class="activity-name">${act.title}</div>
                  <div class="activity-desc">${act.description}</div>
                  <div class="activity-loc">📍 ${act.location} ${act.cost ? `• Est. Cost: $${act.cost.toFixed(2)}` : ''}</div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      });
    }

    itineraryDetailsContainer.innerHTML = html;
  }

  // 4. Admin Dashboard HITL Queue Interactions
  const refreshPendingBtn = document.getElementById('btn-refresh-pending');
  const adminQueueList = document.getElementById('admin-queue-list');

  async function fetchPendingApprovals() {
    adminQueueList.innerHTML = '<p class="empty-state">Fetching queue approvals...</p>';
    try {
      const response = await fetch(`${API_BASE_URL}/api/pending`);
      if (!response.ok) {
        throw new Error('Failed to load pending proposals');
      }
      const data = await response.json();
      renderPendingApprovals(data);
    } catch (err) {
      adminQueueList.innerHTML = `<p class="empty-state" style="color: var(--color-accent);">Error loading dashboard queue: ${err.message}</p>`;
    }
  }

  function renderPendingApprovals(queue) {
    if (!queue || queue.length === 0) {
      adminQueueList.innerHTML = '<p class="empty-state">No pending proposals awaiting verification.</p>';
      return;
    }

    adminQueueList.innerHTML = '';
    queue.forEach(item => {
      const card = document.createElement('div');
      card.className = 'proposal-card';

      const evalResult = item.evaluation || { score: 0, passed: false, feedback: 'No evaluation provided.' };
      const itinerary = item.itinerary || { destination: 'Unknown', summary: '', total_estimated_cost: 0 };

      card.innerHTML = `
        <div class="proposal-header">
          <div>
            <h3 style="font-family: var(--font-family-display); font-size: 1.25rem; font-weight: 700; color: var(--text-primary);">${itinerary.destination} Proposal</h3>
            <span style="font-size: 0.85rem; color: var(--text-muted);">Request ID: ${item.request_id}</span>
          </div>
          <div>
            <span class="meta-tag">Estimated Cost: <strong>$${itinerary.total_estimated_cost.toFixed(2)}</strong></span>
          </div>
        </div>

        <p style="font-size: 0.95rem; font-weight: 600; margin-bottom: 0.5rem;">User Preference Prompt:</p>
        <div class="proposal-prompt">"${item.query}"</div>

        <p style="font-size: 0.95rem; font-weight: 600; margin-bottom: 0.75rem;">LLM-as-a-Judge Evaluation Metrics:</p>
        <div class="scores-container">
          <div class="score-widget">
            <div style="font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase;">Overall Score</div>
            <div class="score-val ${evalResult.passed ? 'score-passed' : 'score-failed'}">${(evalResult.score * 100).toFixed(0)}%</div>
          </div>
          <div class="score-widget">
            <div style="font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase;">Feasibility</div>
            <div class="score-val" style="color: var(--color-secondary);">${(evalResult.feasibility_rating * 100).toFixed(0)}%</div>
          </div>
          <div class="score-widget">
            <div style="font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase;">Quality</div>
            <div class="score-val" style="color: var(--color-secondary);">${(evalResult.quality_rating * 100).toFixed(0)}%</div>
          </div>
          <div class="score-widget">
            <div style="font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase;">Constraint Adherence</div>
            <div class="score-val" style="color: var(--color-secondary);">${(evalResult.constraint_adherence * 100).toFixed(0)}%</div>
          </div>
        </div>

        <div class="eval-feedback">
          <strong>Judge Feedback:</strong> ${evalResult.feedback}
        </div>

        <div class="proposal-actions">
          <button class="btn btn-success btn-sm btn-approve" data-id="${item.request_id}">✓ Approve & Present</button>
          <button class="btn btn-danger btn-sm btn-reject" data-id="${item.request_id}">✗ Reject Proposal</button>
        </div>
      `;

      adminQueueList.appendChild(card);
    });

    // Attach actions
    const approveBtns = adminQueueList.querySelectorAll('.btn-approve');
    approveBtns.forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.target.getAttribute('data-id');
        e.target.disabled = true;
        e.target.textContent = 'Approving...';
        await handleApprove(id);
      });
    });

    const rejectBtns = adminQueueList.querySelectorAll('.btn-reject');
    rejectBtns.forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.target.getAttribute('data-id');
        const reason = prompt("Enter a rejection reason for the client (optional):");
        if (reason === null) return; // user cancelled prompt
        e.target.disabled = true;
        e.target.textContent = 'Rejecting...';
        await handleReject(id, reason);
      });
    });
  }

  async function handleApprove(id) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/approve/${id}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Approve API error');
      await fetchPendingApprovals();
    } catch (err) {
      alert(`Approval failed: ${err.message}`);
      await fetchPendingApprovals();
    }
  }

  async function handleReject(id, reason) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/reject/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: reason || null })
      });
      if (!response.ok) throw new Error('Reject API error');
      await fetchPendingApprovals();
    } catch (err) {
      alert(`Rejection failed: ${err.message}`);
      await fetchPendingApprovals();
    }
  }

  refreshPendingBtn.addEventListener('click', fetchPendingApprovals);
});
