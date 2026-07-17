// AeroPlan AI - Frontend Core Logic
console.log('AeroPlan AI Client successfully initialized.');

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('itinerary-form');
  const promptInput = document.getElementById('prompt');

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const promptValue = promptInput.value.trim();
      if (promptValue) {
        alert(`Generating itinerary for: "${promptValue}"\n\n(Backend implementation will process this request in future phases!)`);
      }
    });
  }
});
