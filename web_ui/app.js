const API_BASE = 'http://127.0.0.1:5000/api';

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatHistory = document.getElementById('chat-history');
    const monitorBtn = document.getElementById('monitor-btn');
    const alertsFeed = document.getElementById('alerts-feed');
    
    // UI Update functions
    function updatePreferencesUI(prefs) {
        document.getElementById('home-airport').textContent = prefs.home_airport || 'None';
        document.getElementById('max-price').textContent = `$${prefs.max_price}`;
        document.getElementById('dep-pref').textContent = prefs.departure_time_preference;
        document.getElementById('ret-pref').textContent = prefs.return_time_preference;
        
        const destList = document.getElementById('destinations-list');
        destList.innerHTML = '';
        if (prefs.destinations && prefs.destinations.length > 0) {
            prefs.destinations.forEach(dest => {
                const span = document.createElement('span');
                span.className = 'tag';
                span.textContent = dest;
                destList.appendChild(span);
            });
        } else {
            destList.innerHTML = '<span class="tag">None</span>';
        }
    }

    function addChatMessage(message, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        msgDiv.textContent = message;
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function renderAlerts(alerts) {
        if (!alerts || alerts.length === 0) return;
        
        // Remove empty state if present
        const emptyState = alertsFeed.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }

        alerts.forEach(deal => {
            const card = document.createElement('div');
            card.className = 'deal-card';
            card.innerHTML = `
                <div>
                    <div class="route">${deal.origin} ➔ ${deal.destination}</div>
                    <div class="details">
                        ${deal.airline} • ${deal.outbound_date} to ${deal.return_date}<br>
                        Outbound: ${deal.outbound_time} | Return: ${deal.return_time} | ${deal.is_direct ? 'Direct' : '1+ Stops'}
                    </div>
                </div>
                <div class="price">$${deal.price}</div>
            `;
            alertsFeed.prepend(card); // Add to top
        });
    }

    // Initial State Fetch
    fetch(`${API_BASE}/state`)
        .then(res => res.json())
        .then(data => {
            updatePreferencesUI(data.preferences);
            if(data.alerts && data.alerts.length > 0) {
                renderAlerts(data.alerts);
            }
        })
        .catch(err => console.error("Could not fetch initial state:", err));

    // Chat Submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;

        addChatMessage(message, 'user');
        chatInput.value = '';

        try {
            const res = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            const data = await res.json();
            
            addChatMessage(data.response, 'assistant');
            updatePreferencesUI(data.state.preferences);
            
        } catch (err) {
            addChatMessage("Sorry, I couldn't reach the agent backend.", 'assistant');
        }
    });

    // Monitor Trigger
    monitorBtn.addEventListener('click', async () => {
        monitorBtn.textContent = 'Checking...';
        monitorBtn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/monitor`, { method: 'POST' });
            const data = await res.json();
            
            if (data.result.status === 'success' && data.result.new_deals_found > 0) {
                renderAlerts(data.result.deals);
                addChatMessage(`I found ${data.result.new_deals_found} new deals! Check your feed.`, 'assistant');
            } else if (data.result.status === 'success') {
                addChatMessage(`I checked, but didn't find any deals under your max price right now.`, 'assistant');
            } else {
                 addChatMessage(`Error checking flights: ${data.result.message}`, 'assistant');
            }
        } catch (err) {
            addChatMessage("Error connecting to the backend to check flights.", 'assistant');
        } finally {
            monitorBtn.textContent = 'Check Flights Now';
            monitorBtn.disabled = false;
        }
    });
});
