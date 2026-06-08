/**
 * CleanTrack AI — Global JavaScript
 * File: static/js/main.js
 */
// ─── Auto-dismiss Flash Alerts ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      dismissAlert(alert);
    }, 5000);
  });
  // Close button on alerts
  document.querySelectorAll('.alert-close').forEach(function (btn) {
    btn.addEventListener('click', function () {
      dismissAlert(btn.closest('.alert'));
    });
  });
});
function dismissAlert(alert) {
  if (!alert) return;
  alert.style.opacity = '0';
  alert.style.transform = 'translateX(100%)';
  alert.style.transition = 'all 0.3s ease';
  setTimeout(function () {
    alert.remove();
  }, 300);
}
// ─── GPS Geolocation ──────────────────────────────────────────────────────────
function getLocation() {
  var statusEl  = document.getElementById('gps-status-text');
  var latInput  = document.getElementById('latitude');
  var lngInput  = document.getElementById('longitude');
  var gpsBtn    = document.getElementById('gps-btn');
  var coordsEl  = document.getElementById('coords-display');
  var mapEl     = document.getElementById('map-container');
  if (!navigator.geolocation) {
    if (statusEl) statusEl.textContent = 'Geolocation not supported by your browser.';
    return;
  }
  if (statusEl) {
    statusEl.textContent = '📡 Fetching your location...';
    statusEl.className = 'gps-status loading';
  }
  if (gpsBtn) {
    gpsBtn.disabled = true;
    gpsBtn.innerHTML = '<span class="spinner"></span> Locating...';
  }
  navigator.geolocation.getCurrentPosition(
    function (position) {
      var lat = position.coords.latitude.toFixed(6);
      var lng = position.coords.longitude.toFixed(6);
      if (latInput)  latInput.value  = lat;
      if (lngInput)  lngInput.value  = lng;
      if (statusEl) {
        statusEl.textContent = '✅ Location captured: ' + lat + ', ' + lng;
        statusEl.className = 'gps-status success';
      }
      if (coordsEl) {
        coordsEl.textContent = lat + ', ' + lng;
        coordsEl.style.display = 'inline';
      }
      // Show map preview
      if (mapEl) {
        mapEl.innerHTML =
          '<iframe src="https://maps.google.com/maps?q=' + lat + ',' + lng +
          '&z=15&output=embed" allowfullscreen loading="lazy"></iframe>';
      }
      if (gpsBtn) {
        gpsBtn.disabled = false;
        gpsBtn.innerHTML = '✅ Location Captured';
        gpsBtn.style.background = 'rgba(34,197,94,0.15)';
        gpsBtn.style.borderColor = 'rgba(34,197,94,0.4)';
        gpsBtn.style.color = '#86efac';
      }
    },
    function (error) {
      var msg = 'Location access denied.';
      if (error.code === 1) msg = '❌ Location access denied. Please allow location access.';
      else if (error.code === 2) msg = '❌ Location unavailable.';
      else if (error.code === 3) msg = '❌ Location request timed out.';
      if (statusEl) {
        statusEl.textContent = msg;
        statusEl.className = 'gps-status error';
      }
      if (gpsBtn) {
        gpsBtn.disabled = false;
        gpsBtn.innerHTML = '📍 Retry Location';
      }
    },
    { timeout: 10000, enableHighAccuracy: true }
  );
}
// ─── Image Preview ────────────────────────────────────────────────────────────
function previewImage(input) {
  var preview = document.getElementById('imagePreview');
  var img     = document.getElementById('previewImg');
  var label   = document.getElementById('upload-label');
  if (input.files && input.files[0]) {
    var reader = new FileReader();
    reader.onload = function (e) {
      if (img)    img.src = e.target.result;
      if (preview) preview.style.display = 'block';
      if (label)  label.textContent = input.files[0].name;
    };
    reader.readAsDataURL(input.files[0]);
  }
}
// ─── Drag and Drop Upload ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  var uploadArea = document.getElementById('upload-area');
  if (!uploadArea) return;
  uploadArea.addEventListener('dragover', function (e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
  });
  uploadArea.addEventListener('dragleave', function () {
    uploadArea.classList.remove('dragover');
  });
  uploadArea.addEventListener('drop', function (e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    var files = e.dataTransfer.files;
    var input = document.getElementById('image-input');
    if (input && files.length > 0) {
      input.files = files;
      previewImage(input);
    }
  });
});
// ─── Modal Helpers ────────────────────────────────────────────────────────────
function openModal(id) {
  var modal = document.getElementById(id);
  if (modal) modal.classList.add('open');
}
function closeModal(id) {
  var modal = document.getElementById(id);
  if (modal) modal.classList.remove('open');
}
// Close modal on overlay click
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) {
        overlay.classList.remove('open');
      }
    });
  });
});
// ─── Form Submission Loading State ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  var submitForm = document.getElementById('complaint-form');
  if (submitForm) {
    submitForm.addEventListener('submit', function () {
      var btn = submitForm.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Submitting & Analyzing...';
      }
    });
  }
});
// ─── Complaint Search (Citizen Track) ────────────────────────────────────────
function searchComplaint() {
  var idInput = document.getElementById('search-id');
  var resultDiv = document.getElementById('search-result');
  var id = idInput ? idInput.value.trim() : '';
  if (!id || isNaN(id)) {
    if (resultDiv) resultDiv.innerHTML =
      '<div class="alert alert-error">⚠️ Please enter a valid complaint ID number.</div>';
    return;
  }
  if (resultDiv) resultDiv.innerHTML =
    '<div style="text-align:center;padding:2rem;color:var(--clr-text-muted)">' +
    '<span class="spinner"></span> Searching...</div>';
  fetch('/api/complaints/search?id=' + id)
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.error) {
        resultDiv.innerHTML =
          '<div class="alert alert-error">❌ ' + data.error + '</div>';
        return;
      }
      var statusClass = {
        'Pending': 'badge-pending',
        'In Progress': 'badge-progress',
        'Resolved': 'badge-resolved',
        'Escalated': 'badge-escalated'
      }[data.status] || 'badge-pending';
      resultDiv.innerHTML =
        '<div class="card" style="margin-top:1.5rem">' +
        '<div class="d-flex justify-between align-center mb-2">' +
        '<h3 style="font-size:1.1rem">Complaint #' + data.id + '</h3>' +
        '<span class="badge ' + statusClass + '">' + data.status + '</span>' +
        '</div>' +
        '<p class="text-muted text-sm mb-2">📅 Submitted: ' + data.date + '</p>' +
        (data.description ? '<p class="mb-2">' + data.description + '</p>' : '') +
        '<p class="text-sm"><span class="ai-' +
        (data.ai_result === 'Garbage Detected' ? 'detected' : 'clean') + '">' +
        '🤖 AI: ' + (data.ai_result || 'N/A') + '</span></p>' +
        (data.image ?
          '<div class="complaint-image-wrap mt-2">' +
          '<img src="/uploads/' + data.image + '" alt="Complaint image">' +
          '</div>' : '') +
        '<a href="/track/' + data.id + '" class="btn btn-secondary btn-sm mt-2">View Full Details →</a>' +
        '</div>';
    })
    .catch(function () {
      if (resultDiv) resultDiv.innerHTML =
        '<div class="alert alert-error">❌ Network error. Please try again.</div>';
    });
}
// Allow Enter key in search input
document.addEventListener('DOMContentLoaded', function () {
  var searchInput = document.getElementById('search-id');
  if (searchInput) {
    searchInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') searchComplaint();
    });
  }
});
// ─── Number Counter Animation ─────────────────────────────────────────────────
function animateCounter(el) {
  var target = parseInt(el.getAttribute('data-target'), 10);
  var duration = 1200;
  var start = 0;
  var startTime = null;
  function step(timestamp) {
    if (!startTime) startTime = timestamp;
    var progress = Math.min((timestamp - startTime) / duration, 1);
    var eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.floor(eased * target);
    if (progress < 1) requestAnimationFrame(step);
    else el.textContent = target;
  }
  requestAnimationFrame(step);
}
document.addEventListener('DOMContentLoaded', function () {
  var counters = document.querySelectorAll('[data-target]');
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  counters.forEach(function (counter) {
    observer.observe(counter);
  });
});
