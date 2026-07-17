// ---------------------------------------------------------
// State
// ---------------------------------------------------------
const state = {
  current: null,      // { name, artist, preview_url }
  recent: [],          // last played tracks
};

// ---------------------------------------------------------
// DOM refs
// ---------------------------------------------------------
const browseGrid = document.getElementById("browse-grid");
const browseEmpty = document.getElementById("browse-empty");
const browseSection = document.getElementById("browse-section");

const suggestSection = document.getElementById("suggest-section");
const suggestGrid = document.getElementById("suggest-grid");
const suggestEmpty = document.getElementById("suggest-empty");
const suggestLoading = document.getElementById("suggest-loading");
const suggestSource = document.getElementById("suggest-source");
const backToBrowseBtn = document.getElementById("back-to-browse");

const searchInput = document.getElementById("search-input");
const recentList = document.getElementById("recent-list");

const audio = document.getElementById("audio");
const playerArt = document.getElementById("player-art");
const playerName = document.getElementById("player-name");
const playerArtist = document.getElementById("player-artist");
const playPauseBtn = document.getElementById("play-pause-btn");
const iconPlay = document.getElementById("icon-play");
const iconPause = document.getElementById("icon-pause");
const progressBar = document.getElementById("progress-bar");
const timeCurrent = document.getElementById("time-current");
const timeTotal = document.getElementById("time-total");
const volumeBar = document.getElementById("volume-bar");
const toastHost = document.getElementById("toast");

audio.volume = 0.7;

// ---------------------------------------------------------
// Helpers
// ---------------------------------------------------------
function hashCode(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (h << 5) - h + str.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

function vinylGradient(seed) {
  const h1 = hashCode(seed) % 360;
  const h2 = (h1 + 40) % 360;
  return `conic-gradient(from 45deg, hsl(${h1},55%,42%), hsl(${h2},60%,20%), hsl(${h1},55%,42%))`;
}

function formatTime(sec) {
  if (!isFinite(sec) || sec < 0) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

function showToast(name, artist) {
  const el = document.createElement("div");
  el.className = "toast-item";
  el.innerHTML = `Now playing <b>${escapeHtml(name)}</b><br><span style="color:var(--text-faint)">${escapeHtml(artist)}</span>`;
  toastHost.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

// ---------------------------------------------------------
// Card rendering
// ---------------------------------------------------------
function buildCard(track) {
  const card = document.createElement("div");
  card.className = "song-card";
  card.tabIndex = 0;

  const isPlaying = state.current && state.current.name === track.name && state.current.artist === track.artist;
  if (isPlaying) card.classList.add("playing");

  card.innerHTML = `
    <div class="art-wrap" style="background:${vinylGradient(track.name + track.artist)}">
      <div class="play-overlay">
        <div class="play-circle">
          <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
        </div>
      </div>
    </div>
    <div class="s-name">${escapeHtml(track.name)}</div>
    <div class="s-artist">${escapeHtml(track.artist)}</div>
  `;

  const trigger = () => playTrack(track);
  card.addEventListener("click", trigger);
  card.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); trigger(); }
  });

  return card;
}

function renderGrid(container, tracks) {
  container.innerHTML = "";
  tracks.forEach((t) => container.appendChild(buildCard(t)));
}

// ---------------------------------------------------------
// Browse / search
// ---------------------------------------------------------
let searchDebounce = null;

async function loadBrowse(query = "") {
  try {
    const res = await fetch(`/api/songs?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    if (data.length === 0) {
      browseGrid.innerHTML = "";
      browseEmpty.classList.remove("hidden");
    } else {
      browseEmpty.classList.add("hidden");
      renderGrid(browseGrid, data);
    }
  } catch (err) {
    console.error("Failed to load songs", err);
  }
}

searchInput.addEventListener("input", () => {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(() => loadBrowse(searchInput.value.trim()), 250);
});

// ---------------------------------------------------------
// Recommendations
// ---------------------------------------------------------
async function loadRecommendations(track) {
  browseSection.classList.add("hidden");
  suggestSection.classList.remove("hidden");
  suggestSource.textContent = `${track.name} — ${track.artist}`;
  suggestGrid.innerHTML = "";
  suggestEmpty.classList.add("hidden");
  suggestLoading.classList.remove("hidden");

  try {
    const params = new URLSearchParams({ song_name: track.name, artist_name: track.artist });
    const res = await fetch(`/api/recommend?${params.toString()}`);
    const data = await res.json();
    suggestLoading.classList.add("hidden");

    if (!res.ok || !Array.isArray(data) || data.length === 0) {
      suggestEmpty.classList.remove("hidden");
      return;
    }
    renderGrid(suggestGrid, data);
  } catch (err) {
    suggestLoading.classList.add("hidden");
    suggestEmpty.classList.remove("hidden");
    console.error("Failed to load recommendations", err);
  }
}

backToBrowseBtn.addEventListener("click", () => {
  suggestSection.classList.add("hidden");
  browseSection.classList.remove("hidden");
});

// ---------------------------------------------------------
// Recently played
// ---------------------------------------------------------
function pushRecent(track) {
  state.recent = state.recent.filter(
    (t) => !(t.name === track.name && t.artist === track.artist)
  );
  state.recent.unshift(track);
  state.recent = state.recent.slice(0, 8);
  renderRecent();
}

function renderRecent() {
  if (state.recent.length === 0) {
    recentList.innerHTML = `<li class="recent-empty">Nothing yet — play a track to start your session.</li>`;
    return;
  }
  recentList.innerHTML = "";
  state.recent.forEach((t) => {
    const li = document.createElement("li");
    li.className = "recent-item";
    li.tabIndex = 0;
    li.innerHTML = `<span class="rname">${escapeHtml(t.name)}</span><span class="rartist">${escapeHtml(t.artist)}</span>`;
    li.addEventListener("click", () => playTrack(t));
    recentList.appendChild(li);
  });
}

// ---------------------------------------------------------
// Player
// ---------------------------------------------------------
function playTrack(track) {
  state.current = track;

  playerName.textContent = track.name;
  playerArtist.textContent = track.artist;
  playerArt.style.background = vinylGradient(track.name + track.artist);
  playerArt.innerHTML = '<div class="vinyl-hole"></div>';

  showToast(track.name, track.artist);
  pushRecent(track);
  loadRecommendations(track);

  if (track.preview_url) {
    audio.src = track.preview_url;
    audio.play().catch(() => {});
    playPauseBtn.disabled = false;
    progressBar.disabled = false;
  } else {
    audio.removeAttribute("src");
    playPauseBtn.disabled = true;
    progressBar.disabled = true;
    setPlayingUI(false);
  }
}

function setPlayingUI(isPlaying) {
  iconPlay.classList.toggle("hidden", isPlaying);
  iconPause.classList.toggle("hidden", !isPlaying);
  playerArt.classList.toggle("spinning", isPlaying);
}

playPauseBtn.addEventListener("click", () => {
  if (!state.current || !state.current.preview_url) return;
  if (audio.paused) audio.play();
  else audio.pause();
});

audio.addEventListener("play", () => setPlayingUI(true));
audio.addEventListener("pause", () => setPlayingUI(false));
audio.addEventListener("ended", () => setPlayingUI(false));

audio.addEventListener("timeupdate", () => {
  if (!audio.duration) return;
  progressBar.value = (audio.currentTime / audio.duration) * 100;
  timeCurrent.textContent = formatTime(audio.currentTime);
  timeTotal.textContent = formatTime(audio.duration);
});

progressBar.addEventListener("input", () => {
  if (!audio.duration) return;
  audio.currentTime = (progressBar.value / 100) * audio.duration;
});

volumeBar.addEventListener("input", () => {
  audio.volume = volumeBar.value / 100;
});

// ---------------------------------------------------------
// Init
// ---------------------------------------------------------
loadBrowse();