<script lang="ts">  
  import { onMount, tick } from 'svelte';
  import { supabase } from '../lib/supabaseClient';
  import countryNames from '../lib/country_names.json';

  $effect(() => {
  const code = roomCode;

  if (!code) return;

  void refreshPauseState();

  const timer = window.setInterval(() => {
    void refreshPauseState();
  }, 2000);

  return () => window.clearInterval(timer);
});

function countryName(tag: string | null | undefined): string {
  if (!tag) return 'Nie wybrano';
  return countryNames[tag as keyof typeof countryNames] ?? tag;
}


type Player = {
  name: string;
  ban: string | null;
  country: string | null;
};

type DraftRoomData = {
  id: string;
  code: string;
  phase: 'ban' | 'pick';
  current_turn: number;
  is_paused: boolean;
  players: {
    id: string;
    seat: number;
    name: string;
    ban_country: string | null;
    picked_country: string | null;
  }[];
};

let isDraftPaused = $state(false);


  type Province = {
    owner: string;
    name: string;
    id: string;
  };

  let phase: 'ban' | 'pick' = $state('ban');
  let currentTurn = $state(0);

  let players: Player[] = $state([
  ]);

 let roomCode = $state('NANOKA');
let playerToken = $state<string | null>(null);
  let mapSvg = $state('');
  let mapError = $state('');
  let connectionText = $state('Łączenie z bazą…');
  let isSaving = $state(false);
  let hoveredProvince = $state<Province | null>(null);
  let selectedMessage = $state(
    'Kliknij prowincję, aby rozpoznać państwo.'
  );

  let mapStage: HTMLDivElement;
  let hoveredOwner: string | null = null;


type PendingCountryAction = {
  owner: string;
  provinceName: string;
  action: 'ban' | 'pick';
  turnIndex: number;
};

let pendingCountryAction = $state<PendingCountryAction | null>(null);
let showDraftResults = $state(false);


    // Zoom i przesuwanie widoku mapy.
  const MAP_X = 2380;
  const MAP_Y = 0;
  const MAP_WIDTH = 3252;
  const MAP_HEIGHT = 2048;
  const MAX_ZOOM = 8;

  let currentViewBox = {
    x: MAP_X,
    y: MAP_Y,
    width: MAP_WIDTH,
    height: MAP_HEIGHT
  };

  function getMapSvg(): SVGSVGElement | null {
    return mapStage?.querySelector('svg.world-map-svg') ?? null;
  }

  function clampViewBox() {
    const vb = currentViewBox;

    vb.width = Math.min(MAP_WIDTH, Math.max(MAP_WIDTH / MAX_ZOOM, vb.width));
    vb.height = Math.min(MAP_HEIGHT, Math.max(MAP_HEIGHT / MAX_ZOOM, vb.height));

    vb.x = Math.max(MAP_X, Math.min(MAP_X + MAP_WIDTH - vb.width, vb.x));
    vb.y = Math.max(MAP_Y, Math.min(MAP_Y + MAP_HEIGHT - vb.height, vb.y));
  }

  function applyViewBox() {
    const svg = getMapSvg();
    if (!svg) return;

    clampViewBox();

    svg.setAttribute(
      'viewBox',
      `${currentViewBox.x} ${currentViewBox.y} ${currentViewBox.width} ${currentViewBox.height}`
    );
  }

  function handleMapWheel(event: WheelEvent) {
    const svg = getMapSvg();
    if (!svg) return;

    // Scroll nad mapą przybliża lub oddala, zamiast przewijać stronę.
    event.preventDefault();

    const rect = svg.getBoundingClientRect();

    // Zamień pozycję kursora z pikseli ekranu na współrzędne SVG.
    const point = svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;

    const matrix = svg.getScreenCTM();
    if (!matrix) return;

    const cursor = point.matrixTransform(matrix.inverse());

    const old = { ...currentViewBox };

    // Płynne przybliżanie i oddalanie.
    const factor = event.deltaY < 0 ? 1 / 1.2 : 1.2;

    const newWidth = Math.min(
      MAP_WIDTH,
      Math.max(MAP_WIDTH / MAX_ZOOM, old.width * factor)
    );

    const newHeight = Math.min(
      MAP_HEIGHT,
      Math.max(MAP_HEIGHT / MAX_ZOOM, old.height * factor)
    );

    // Kursor pozostaje nad tym samym punktem mapy.
    const ratioX = (cursor.x - old.x) / old.width;
    const ratioY = (cursor.y - old.y) / old.height;

    currentViewBox = {
      x: cursor.x - ratioX * newWidth,
      y: cursor.y - ratioY * newHeight,
      width: newWidth,
      height: newHeight
    };

    applyViewBox();
  }

  function resetMapZoom() {
    currentViewBox = {
      x: MAP_X,
      y: MAP_Y,
      width: MAP_WIDTH,
      height: MAP_HEIGHT
    };

    applyViewBox();
  }

  const currentPlayer = $derived(players[currentTurn]);

  onMount(() => {
  let syncTimer: ReturnType<typeof setInterval> | undefined;

  const initialize = async () => {
    try {
    
const params = new URLSearchParams(window.location.search);

const requestedRoom = params.get('room')?.trim();

if (requestedRoom) {
  roomCode = requestedRoom.toUpperCase();
}

const hashParams = new URLSearchParams(
  window.location.hash.slice(1)
);

const storageKey = `draftout-player-token:${roomCode}`;
const tokenFromUrl = hashParams.get('token');

if (tokenFromUrl && /^[0-9a-f]{64}$/i.test(tokenFromUrl)) {
  playerToken = tokenFromUrl;

  // Zachowaj token na czas bieżącej sesji karty.
  sessionStorage.setItem(storageKey, tokenFromUrl);
} else {
  // Po odświeżeniu odzyskaj token zapisany wcześniej.
  const savedToken = sessionStorage.getItem(storageKey);

  playerToken =
    savedToken && /^[0-9a-f]{64}$/i.test(savedToken)
      ? savedToken
      : null;
}

// Usuń token z widocznego adresu, ale zachowaj go w sesji.
if (hashParams.has('token')) {
  window.history.replaceState(
    null,
    '',
    `${window.location.pathname}${window.location.search}`
  );
}



    const response = await fetch('/eu4_world_map_cropped.svg');

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const source = await response.text();
      const parser = new DOMParser();
      const documentSvg = parser.parseFromString(
        source,
        'image/svg+xml'
      );
      const svg = documentSvg.documentElement;

    svg.setAttribute('viewBox', '2380 0 3252 2048');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    svg.setAttribute('overflow', 'hidden');

     currentViewBox = {
        x: MAP_X,
        y: MAP_Y,
        width: MAP_WIDTH,
        height: MAP_HEIGHT
      };
      
      if (svg.querySelector('parsererror')) {
        throw new Error('Nie udało się odczytać pliku SVG.');
      }

      const ns = 'http://www.w3.org/2000/svg';

      // Definicje wzorów SVG.
      const defs = documentSvg.createElementNS(ns, 'defs');

      // Wzór bana: szare tło i jasne ukośne paski.
      const banPattern = documentSvg.createElementNS(ns, 'pattern');

      banPattern.setAttribute('id', 'draftout-ban-pattern');
      banPattern.setAttribute('width', '8');
      banPattern.setAttribute('height', '8');
      banPattern.setAttribute('patternUnits', 'userSpaceOnUse');
      banPattern.setAttribute('patternTransform', 'rotate(45)');

      const banBase = documentSvg.createElementNS(ns, 'rect');
      banBase.setAttribute('width', '8');
      banBase.setAttribute('height', '8');
      banBase.setAttribute('fill', '#626c77');

      const banStripe = documentSvg.createElementNS(ns, 'rect');
      banStripe.setAttribute('width', '3');
      banStripe.setAttribute('height', '8');
      banStripe.setAttribute('fill', '#b8c0c9');

      banPattern.append(banBase, banStripe);

      // Wzór wyboru: półprzezroczyste białe paski.
      // Przezroczyste odstępy pozwalają zachować oryginalny kolor mapy.
      const pickedPattern = documentSvg.createElementNS(
        ns,
        'pattern'
      );

      pickedPattern.setAttribute('id', 'draftout-picked-pattern');
      pickedPattern.setAttribute('width', '8');
      pickedPattern.setAttribute('height', '8');
      pickedPattern.setAttribute('patternUnits', 'userSpaceOnUse');
      pickedPattern.setAttribute('patternTransform', 'rotate(45)');

      const pickedStripe = documentSvg.createElementNS(ns, 'rect');
      pickedStripe.setAttribute('width', '2');
      pickedStripe.setAttribute('height', '8');
    pickedStripe.setAttribute('fill', '#000000');
    pickedStripe.setAttribute('fill-opacity', '0.85');

      pickedPattern.append(pickedStripe);
      defs.append(banPattern, pickedPattern);
      svg.insertBefore(defs, svg.firstChild);

      svg.classList.add('world-map-svg');

      // Warstwa nakładek zostanie umieszczona nad mapą.
      const overlayGroup = documentSvg.createElementNS(ns, 'g');
      overlayGroup.setAttribute('class', 'picked-overlay-group');
      overlayGroup.setAttribute('pointer-events', 'none');

      for (const path of svg.querySelectorAll('path')) {
        const title = path.querySelector('title')?.textContent ?? '';
        const ownerMatch = title.match(
          /pa.{0,4}stwo:\s*([A-Z]{3})\s*$/i
        );
        const provinceMatch = title.match(
          /^(.*?)\s*\|\s*ID\s*(\d+)/
        );

        if (!ownerMatch) continue;

        const owner = ownerMatch[1];

        path.dataset.owner = owner;
        path.dataset.province =
          provinceMatch?.[1] ?? 'Unknown province';
        path.dataset.provinceId = provinceMatch?.[2] ?? '';
        path.classList.add('interactive-province');

        // Kopia geometrii prowincji, używana tylko jako nakładka.
        const overlay = path.cloneNode(false) as SVGPathElement;

        overlay.removeAttribute('id');
        overlay.setAttribute('class', 'picked-overlay');
        overlay.dataset.owner = owner;
        overlay.setAttribute(
          'fill',
          'url(#draftout-picked-pattern)'
        );
        overlay.setAttribute('stroke', 'none');
        overlay.setAttribute('display', 'none');

        overlayGroup.append(overlay);
      }

      // Nakładki rysujemy nad wszystkimi prowincjami mapy.
      svg.append(overlayGroup);

      // Przytnij geometrię mapy do widocznego obszaru Europy, Afryki i Azji
const cropDefs = svg.querySelector('defs');

if (cropDefs) {
  let clipPath = svg.querySelector('#draftout-map-crop') as SVGClipPathElement | null;

  if (!clipPath) {
    clipPath = document.createElementNS(
      'http://www.w3.org/2000/svg',
      'clipPath'
    );
    clipPath.id = 'draftout-map-crop';
    clipPath.setAttribute('clipPathUnits', 'userSpaceOnUse');

    const rect = document.createElementNS(
      'http://www.w3.org/2000/svg',
      'rect'
    );

    rect.setAttribute('x', '2380');
    rect.setAttribute('y', '0');
    rect.setAttribute('width', '3252');
    rect.setAttribute('height', '2048');

    clipPath.appendChild(rect);
    cropDefs.appendChild(clipPath);
  }
}

    mapSvg = new XMLSerializer().serializeToString(svg);

    await tick();
    await loadDraftFromDatabase();

    // Synchronizuj stan draftu między graczami co 2 sekundy.
    syncTimer = window.setInterval(() => {
      void refreshDraftState();
    }, 2000);
  } catch (error) {
    console.error('Map loading error:', error);
    mapError =
      'Nie udało się wczytać mapy. Sprawdź plik static/eu4_world_map.svg.';
  }
  };

  void initialize();

  return () => {
    if (syncTimer !== undefined) {
      window.clearInterval(syncTimer);
    }
  };
})
  


async function applyDraftRoom(room: DraftRoomData) {
  roomCode = room.code;
  phase = room.phase;
  currentTurn = room.current_turn;
  isDraftPaused = room.is_paused;

players = room.players.map((player) => ({
  name: player.name,
  ban: player.ban_country,
  country: player.picked_country
}));

  await tick();


  mapStage
    ?.querySelectorAll<SVGPathElement>('path.interactive-province')
    .forEach((path) => {
      path.classList.remove(
        'country-banned',
        'country-picked',
        'country-hovered'
      );
    });

  mapStage
    ?.querySelectorAll<SVGPathElement>('path.picked-overlay')
    .forEach((path) => {
      path.setAttribute('display', 'none');
    });


  for (const player of players) {
    if (player.ban) {
      setCountryMapState(player.ban, 'banned');
    }

    if (player.country) {
      setCountryMapState(player.country, 'picked');
    }
  }

  // Globalny ban — nie jest przypisany do żadnego gracza.
setCountryMapState('TUR', 'banned');

  showDraftResults =
    players.length > 0 &&
    players.every((player) => player.country !== null);
}


async function loadDraftFromDatabase() {
  connectionText = 'Łączenie z bazą…';

  try {
    const { data: existingRoom, error: loadError } =
      await supabase.rpc('get_draft_room', {
        p_code: roomCode
      });

    if (loadError) throw loadError;

    const room = existingRoom as DraftRoomData | null;

    if (!room) {
      players = [];
      currentTurn = 0;
      phase = 'ban';
      pendingCountryAction = null;
      showDraftResults = false;

      connectionText = 'Nie znaleziono pokoju';
      selectedMessage =
        `Pokój ${roomCode} nie istnieje. Sprawdź kod lub poproś administratora o utworzenie pokoju.`;

      return;
    }

    await applyDraftRoom(room);

    connectionText = 'Połączono z bazą';
    selectedMessage = 'Stan draftu wczytany z Supabase.';
  } catch (error) {
    console.error('Draft database error:', error);

    connectionText = 'Błąd połączenia z bazą';
    selectedMessage =
      'Nie udało się wczytać draftu. Sprawdź połączenie i konsolę.';
  }
}

async function refreshDraftState() {
  if (!roomCode) return;

  try {
    const { data, error } = await supabase.rpc('get_draft_room', {
      p_code: roomCode
    });

    if (error) {
      console.error('Błąd synchronizacji draftu:', error);
      return;
    }

    if (data) {
      applyDraftRoom(data as DraftRoomData);
    }
  } catch (error) {
    console.error('Nie udało się odświeżyć draftu:', error);
  }
}

async function refreshPauseState() {
  try {
    const { data, error } = await supabase.rpc('get_draft_room', {
      p_code: roomCode
    });

    if (error || !data) return;

    const room = data as DraftRoomData;
    isDraftPaused = room.is_paused;
  } catch (error) {
    console.error('Nie udało się odświeżyć stanu pauzy:', error);
  }
}



  function getProvince(target: EventTarget | null): Province | null {
    if (!(target instanceof Element)) return null;

    const path = target.closest<SVGPathElement>(
      'path.interactive-province[data-owner]'
    );

    if (!path || !mapStage?.contains(path)) return null;

    return {
      owner: path.dataset.owner ?? '',
      name: path.dataset.province ?? 'Unknown province',
      id: path.dataset.provinceId ?? ''
    };
  }

  function setCountryMapState(
    owner: string,
    state: 'banned' | 'picked'
  ) {
    if (!mapStage) return;

    // Zmieniamy stan właściwych prowincji mapy.
    const provinces = mapStage.querySelectorAll<SVGPathElement>(
      'path.interactive-province[data-owner]'
    );

    provinces.forEach((path) => {
      if (path.dataset.owner !== owner) return;

      path.classList.remove('country-banned', 'country-picked');
      path.classList.add(
        state === 'banned' ? 'country-banned' : 'country-picked'
      );
    });

    // Paski wyboru pokazujemy tylko dla wybranego państwa.
    const overlays = mapStage.querySelectorAll<SVGPathElement>(
      'path.picked-overlay[data-owner]'
    );

    overlays.forEach((path) => {
      if (path.dataset.owner !== owner) return;

      path.setAttribute(
        'display',
        state === 'picked' ? 'inline' : 'none'
      );
    });
  }

  function handleMapMove(event: PointerEvent) {
    const province = getProvince(event.target);
    hoveredProvince = province;

    if (!mapStage) return;

    mapStage
      .querySelectorAll<SVGPathElement>(
        'path.interactive-province.country-hovered'
      )
      .forEach((path) => path.classList.remove('country-hovered'));

    if (province) {
    mapStage
        .querySelectorAll<SVGPathElement>(
        `path.interactive-province[data-owner="${province.owner}"]`
        )
        .forEach((path) => {
        if (
            !path.classList.contains('country-picked') &&
            !path.classList.contains('country-banned')
        ) {
            path.classList.add('country-hovered');
        }
        });
    }
  }

  function handleMapLeave() {
    hoveredProvince = null;

    mapStage
      ?.querySelectorAll<SVGPathElement>(
        'path.interactive-province.country-hovered'
      )
      .forEach((path) => path.classList.remove('country-hovered'));
  }


async function handleProvinceClick(event: MouseEvent) {
  const province = getProvince(event.target);

  if (!province) return;

  if (isDraftPaused) {
  pendingCountryAction = null;
  selectedMessage = 'Draft jest zapauzowany. Czekamy na wszystkich graczy.';
  return;
}

  if (!(await canCurrentPlayerAct())) {
  return;
}

  if (!playerToken) {
    selectedMessage =
      'Otwórz indywidualny link dostępu otrzymany od organizatora, aby wykonywać ruchy.';
    return;
  }

  if (players.length === 0) {
    selectedMessage = 'Nie ma aktywnego pokoju.';
    return;
  }

  const owner = province.owner;

  const owner = province.owner;

if (owner === 'TUR') {
  pendingCountryAction = null;
  selectedMessage = 'Turcja jest globalnie zbanowana i nie może zostać wybrana.';
  return;
}

const alreadyBanned = players.some(

  const alreadyBanned = players.some(
    (player) => player.ban === owner
  );

  const alreadyPicked = players.some(
    (player) => player.country === owner
  );

  

  if (alreadyBanned || alreadyPicked) {
    selectedMessage = `${owner} jest już zbanowane lub wybrane.`;
    return;
  }

  const player = players[currentTurn];

  if (!player) {
    selectedMessage = 'Nie znaleziono aktualnego gracza.';
    return;
  }

  if (phase === 'ban') {
    if (player.ban) {
      selectedMessage =
        `${player.name} ma już przydzielony ban.`;
      return;
    }
  } else {
    if (player.country) {
      selectedMessage =
        `${player.name} ma już wybrane państwo.`;
      return;
    }
  }

  pendingCountryAction = {
    owner,
    provinceName: province.name,
    action: phase,
    turnIndex: currentTurn
  };
}

let checkingTurn = false;

async function canCurrentPlayerAct(): Promise<boolean> {
  if (!playerToken || checkingTurn) {
    selectedMessage = 'Brak dostępu lub trwa sprawdzanie tury.';
    return false;
  }

  checkingTurn = true;

  try {
console.time('is_player_turn RPC');

const { data, error } = await supabase.rpc('is_player_turn', {
  p_code: roomCode,
  p_token: playerToken
});

console.timeEnd('is_player_turn RPC');

    if (error) {
      console.error('Błąd sprawdzania tury:', error);
      selectedMessage = 'Nie udało się sprawdzić tury.';
      return false;
    }

    if (data !== true) {
      selectedMessage = 'To nie jest Twój ruch.';
      return false;
    }

    return true;
  } finally {
    checkingTurn = false;
  }
}

async function confirmCountryAction() {
  const pending = pendingCountryAction;

  if (!pending || isSaving) return;

  if (isDraftPaused) {
  pendingCountryAction = null;
  selectedMessage = 'Draft jest zapauzowany. Nie można wykonać ruchu.';
  return;
}

  if (
    pending.turnIndex !== currentTurn ||
    pending.action !== phase
  ) {
    pendingCountryAction = null;
    selectedMessage = 'Stan draftu się zmienił. Spróbuj ponownie.';
    await loadDraftFromDatabase();
    return;
  }

  const { owner, provinceName, action, turnIndex } = pending;
  const playerName = players[turnIndex]?.name ?? 'Gracz';

  isSaving = true;
  selectedMessage = 'Zapisywanie ruchu…';

  try {
if (!playerToken) {
  pendingCountryAction = null;
  selectedMessage =
    'Brak tokenu dostępu. Otwórz indywidualny link gracza.';
  return;
}

const { data, error } = await supabase.rpc(
  'submit_draft_action',
  {
    p_code: roomCode,
    p_token: playerToken,
    p_action: action,
    p_country: owner
  }
);

    if (error) throw error;
    if (!data) throw new Error('Baza nie zwróciła stanu draftu.');

    pendingCountryAction = null;

    await applyDraftRoom(data as DraftRoomData);

    selectedMessage =
      action === 'ban'
        ? `${playerName} zbanował państwo ${owner} (prowincja: ${provinceName}).`
        : `${playerName} wybrał państwo ${owner} (prowincja: ${provinceName}).`;

    if (players.every((player) => player.country !== null)) {
      selectedMessage =
        'Draft zakończony! Wszyscy gracze mają swoje państwa.';
    }

    connectionText = 'Połączono z bazą';
  } catch (error) {
    console.error('Nie udało się zapisać ruchu:', error);

    selectedMessage =
      error instanceof Error
        ? `Nie udało się zapisać ruchu: ${error.message}`
        : 'Nie udało się zapisać ruchu. Spróbuj ponownie.';

    connectionText = 'Błąd zapisu';
  } finally {
    isSaving = false;
  }
}



  function nextDemoTurn() {
    if (phase === 'ban') {
      phase = 'pick';
      currentTurn = 0;
    } else {
      currentTurn = (currentTurn + 1) % players.length;
    }
  }


async function resetDraft() {
  if (isSaving) return;

  isSaving = true;
  selectedMessage = 'Resetowanie draftu…';

  try {
    const { data, error } = await supabase.rpc(
      'reset_draft_room',
      { p_code: roomCode }
    );

    if (error) throw error;
    if (!data) throw new Error('Baza nie zwróciła stanu draftu.');

    await applyDraftRoom(data as DraftRoomData);

    pendingCountryAction = null;
    showDraftResults = false;
    hoveredProvince = null;
    selectedMessage = 'Draft został zresetowany w Supabase.';
    connectionText = 'Połączono z bazą';

    resetMapZoom();
  } catch (error) {
    console.error('Nie udało się zresetować draftu:', error);

    selectedMessage =
      error instanceof Error
        ? `Nie udało się zresetować draftu: ${error.message}`
        : 'Nie udało się zresetować draftu.';

    connectionText = 'Błąd zapisu';
  } finally {
    isSaving = false;
  }
}

async function generatePlayerLinks(code: string) {
  const { data, error } = await supabase.rpc(
    'issue_player_tokens',
    { p_code: code }
  );

  if (error) throw error;

  const result = data as {
    code: string;
    players: {
      seat: number;
      name: string;
      token: string;
    }[];
  };

  let issuedLinks: {
  seat: number;
  name: string;
  url: string;
}[] = [];

  issuedLinks = result.players.map((player) => ({
    seat: player.seat,
    name: player.name,
    url:
      `${window.location.origin}/?room=${encodeURIComponent(result.code)}` +
      `#token=${player.token}`
  }));
}
</script>



<svelte:head>
  <title>Draftout</title>
  <meta
    name="description"
    content="Interaktywny draft państw do turniejów Europa Universalis IV."
  />
</svelte:head>

<div class="app-shell">
  <header class="topbar">
    <a class="brand" href="/" aria-label="Draftout — strona główna">
      <span class="brand-mark">D</span>
      <span>DRAFTOUT</span>
    </a>

    <div class="room-info">
      <span class="room-label">POKÓJ</span>
      <span class="room-code">{roomCode}</span>
      <span class="connection-dot"></span>
      <span class="connection-text">{connectionText}</span>
    </div>

    <div class="topbar-right">
      <span class="game-label">EUROPA UNIVERSALIS IV</span>
    </div>
  </header>

  <main class="main-layout">
    <section class="map-section">
      <div class="map-toolbar">
        <div class="phase-info">
          <span class:ban-phase={phase === 'ban'} class:pick-phase={phase === 'pick'} class="phase-indicator">
            <span class="phase-dot"></span>
            {phase === 'ban' ? 'FAZA BANÓW' : 'FAZA WYBORU'}
          </span>
          <span class="toolbar-divider"></span>
          <span class="turn-label">
            RUCH {currentTurn + 1} <span class="muted">/ {players.length}</span>
          </span>
        </div>

        <div class="map-legend">
          <span><i class="legend-dot available"></i>Dostępne</span>
          <span><i class="legend-dot banned"></i>Zbanowane</span>
<span>
  <svg class="legend-picked-swatch" viewBox="0 0 16 16" aria-hidden="true">
    <defs>
      <pattern
        id="legend-picked-pattern"
        width="4"
        height="4"
        patternUnits="userSpaceOnUse"
        patternTransform="rotate(45)"
      >
        <rect
          width="2"
          height="8"
          fill="#000000"
          fill-opacity="0.85"
        />
      </pattern>
    </defs>

    <rect x="0.5" y="0.5" width="15" height="15" rx="2" fill="#ceb561" />
    <rect
      x="0.5"
      y="0.5"
      width="18"
      height="18"
      rx="2"
      fill="url(#legend-picked-pattern)"
    />
    <rect
      x="0.5"
      y="0.5"
      width="18"
      height="18"
      rx="2"
      fill="none"
      stroke="rgba(0, 0, 0, 0.35)"
    />
  </svg>
  Wybrane
</span>
        </div>
      </div>


        <div
          class="map-stage"
          bind:this={mapStage}
          onpointermove={handleMapMove}
          onpointerleave={handleMapLeave}
          onclick={handleProvinceClick}
          onwheel={handleMapWheel}
        >
        <div class="map-background-glow"></div>

        {#if mapSvg}
            <div class="world-map-container">
            {@html mapSvg}
            </div>
        {:else if mapError}
            <div class="map-message error">{mapError}</div>
        {:else}
            <div class="map-message">Wczytywanie mapy…</div>
        {/if}

          <div class="map-overlay-top">
            <span class="map-version">1444</span>

            <button
              class="map-reset-button"
              onclick={resetMapZoom}
              title="Przywróć pełny widok mapy"
            >
              Reset zoomu
            </button>
          </div>

{#if isDraftPaused}
  <div class="draft-paused-overlay" role="status" aria-live="polite">
    <div class="draft-paused-content">
      <div class="draft-paused-icon">Ⅱ</div>
      <h2>Draft zapauzowany</h2>
      <p>Czekamy na wszystkich graczy</p>
    </div>
  </div>
{/if}

        </div>


      <div class="action-bar">
        <div class="turn-player">
          <div class="turn-avatar">{currentPlayer?.name.slice(0, 1) ?? '?'}</div>
          <div>
            <span class="turn-caption">AKTUALNY GRACZ</span>
            <strong>{currentPlayer?.name ?? 'Brak gracza'}</strong>
          </div>
        </div>

        <div class="action-description">
          <strong>{phase === 'ban' ? 'Wybierz kraj do zbanowania' : 'Wybierz kraj do gry'}</strong>
          <span>
            {phase === 'ban'
              ? 'Zbanowane państwo będzie niedostępne dla wszystkich.'
              : 'Wybrane państwo zostanie przypisane do gracza.'}
          </span>
        </div>
      </div>
    </section>

    <section class="players-section">
      <div class="players-heading">
        <div>
          <span class="section-eyebrow">TURNIEJ</span>
          <h2>Gracze <span class="player-count">{players.length}</span></h2>
        </div>
        <span class="order-label">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
          </svg>
        </span>
      </div>

      <div class="players-list">
        {#each players as player, index}
          <article class:active={index === currentTurn} class="player-card">
            <div class="player-number">{String(index + 1).padStart(2, '0')}</div>

            <div class="player-main">
              <div class="player-name-row">
                <span class="player-name">{player.name}</span>
                {#if index === currentTurn}
                  <span class="current-indicator">AKTUALNIE</span>
                {/if}
              </div>

              <div class="player-result">
                <span class="result-label">BAN</span>
                <span class:empty={!player.ban} class="result-value ban-value">
                  {player.ban ? countryName(player.ban) : 'Nie wybrano'}
                </span>
              </div>

              <div class="player-result">
                <span class="result-label">KRAJ</span>
                <span
  class:empty={!player.country}
  class="result-value country-value"
>
  {player.country ? countryName(player.country) : 'Nie wybrano'}
</span>
              </div>
            </div>

            <div class="player-status">
              {#if player.country}
                <span class="status-check" title="Kraj wybrany">✓</span>
              {:else if player.ban}
                <span class="status-ban" title="Ban wykonany">B</span>
              {:else}
                <span class="status-wait" title="Oczekuje">·</span>
              {/if}
            </div>
          </article>
        {/each}
      </div>

      <div class="players-footer">
        <span class="footer-dot"></span>
        <span>KOLEJNOŚĆ OD NAJSŁABSZEGO</span>
      </div>
    </section>

{#if pendingCountryAction}
  <div class="confirm-backdrop">
    <div
      class="confirm-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
    >
      <h2 id="confirm-title">
        {pendingCountryAction.action === 'ban'
          ? 'Potwierdzenie bana'
          : 'Potwierdzenie wyboru'}
      </h2>

    
<p>
  Czy na pewno chcesz
  {pendingCountryAction.action === 'ban'
    ? ' zbanować'
    : ' wybrać'}
  państwo <strong>{countryName(pendingCountryAction.owner)}</strong>?
</p>


      <div class="confirm-actions">
        <button
          class="confirm-cancel"
          onclick={() => pendingCountryAction = null}
        >
          Anuluj
        </button>

        <button
          class="confirm-accept"
          disabled={isSaving}
          onclick={confirmCountryAction}
        >
          {pendingCountryAction.action === 'ban'
            ? 'Potwierdź bana'
            : 'Potwierdź wybór'}
        </button>
      </div>
    </div>
  </div>
{/if}

{#if showDraftResults}
  <div class="results-backdrop">
    <section
      class="results-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="results-title"
    >
      <header class="results-header">
        <div>
          <span class="section-eyebrow">DRAFTOUT / PODSUMOWANIE</span>
          <h2 id="results-title">Wyniki draftu</h2>
          <p>Wszyscy gracze mają już przydzielone państwa.</p>
        </div>

        <span class="results-complete">DRAFT ZAKOŃCZONY</span>
      </header>

      <div class="results-summary">
        <div class="results-stat">
          <span>GRACZE</span>
          <strong>{players.length}</strong>
        </div>

        <div class="results-stat">
          <span>WYBRANE PAŃSTWA</span>
          <strong>
            {players.filter((player) => player.country !== null).length}
            / {players.length}
          </strong>
        </div>

        <div class="results-stat">
          <span>BANY</span>
          <strong>
            {players.filter((player) => player.ban !== null).length}
            / {players.length}
          </strong>
        </div>
      </div>

      <div class="results-table-wrapper">
        <table class="results-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Gracz</th>
              <th>Wybrane państwo</th>
              <th>Zbanowane państwo</th>
            </tr>
          </thead>

          <tbody>
            {#each players as player, index}
              <tr>
                <td class="results-number">
                  {String(index + 1).padStart(2, '0')}
                </td>
                <td class="results-player">{player.name}</td>
                <td>
                  <span class="results-country">
  {player.country ? countryName(player.country) : '—'}
</span>
                </td>
                <td>
<span class="results-ban">
  {player.ban ? countryName(player.ban) : '—'}
</span>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </section>
  </div>
{/if}
  </main>

  <footer class="app-footer">
    <span>DRAFTOUT <span class="footer-muted">/ COMMUNITY TOURNAMENT TOOL</span></span>
    <span>RELASE 1.0</span>
  </footer>
</div>

<style>
 
:global(*) {
  box-sizing: border-box;
}

:global(html) {
  width: 100%;
  height: 100%;
  min-width: 900px;
  min-height: 0;
  margin: 0;
  background: #0b0f14;
}

:global(body) {
  width: 100%;
  height: 100%;
  min-width: 900px;
  min-height: 0;
  margin: 0;
  overflow: hidden;
  color: #e8edf3;
  background: #0b0f14;
  font-family: Inter, "Segoe UI", Arial, sans-serif;
  font-size: 13px;
  -webkit-font-smoothing: antialiased;
}

:global(button) {
  font: inherit;
}

/* Główny układ aplikacji */

.app-shell {
  display: flex;
  width: 100%;
  height: 100vh;
  height: 100dvh;
  min-height: 0;
  flex-direction: column;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 50% -20%, #1b2c3d 0%, transparent 55%),
    #0b0f14;
}

.topbar {
  display: flex;
  height: 62px;
  min-height: 62px;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 0 30px;
  border-bottom: 1px solid #27313d;
  background: rgba(13, 18, 25, 0.96);
}

.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  color: #f1f5f9;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 2px;
  text-decoration: none;
  white-space: nowrap;
}

.brand-mark {
  display: grid;
  width: 29px;
  height: 29px;
  flex-shrink: 0;
  place-items: center;
  border: 1px solid #8298ae;
  background: linear-gradient(145deg, #425a71, #1b2c3c);
  color: #fff;
  font-family: Georgia, serif;
  font-size: 19px;
}

.room-info,
.topbar-right,
.phase-info,
.map-legend,
.order-label {
  display: flex;
  align-items: center;
}

.room-info {
  gap: 10px;
}

.room-label,
.section-eyebrow,
.turn-caption,
.result-label {
  color: #7e8b9b;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1.3px;
}

.room-code {
  padding: 6px 9px;
  border: 1px solid #334152;
  border-radius: 4px;
  background: #151d27;
  color: #dbe5ef;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
}

.connection-dot,
.footer-dot {
  width: 6px;
  height: 6px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #d8a958;
}

.connection-text {
  color: #a4afbd;
  font-size: 11px;
}

.topbar-right {
  gap: 18px;
}

.game-label {
  color: #7f8c9c;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1.3px;
}

.settings-button {
  display: grid;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  place-items: center;
  border: 1px solid #303c49;
  border-radius: 5px;
  background: #151c25;
  color: #9eacbb;
  cursor: pointer;
}

.settings-button svg,
.order-label svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* Główna część: mapa i panel graczy */

.main-layout {
  display: grid;
  flex: 1 1 0;
  grid-template-columns: minmax(0, 1fr) 286px;
  grid-template-rows: minmax(0, 1fr);
  gap: 16px;
  min-width: 0;
  min-height: 0;
  padding: 18px 20px 12px;
  overflow: hidden;
}

.map-section,
.players-section {
  display: flex;
  min-width: 0;
  min-height: 0;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #2a3541;
  border-radius: 7px;
  background: #101720;
}

/* Pasek nad mapą */

.map-toolbar {
  display: flex;
  min-height: 48px;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 16px;
  border-bottom: 1px solid #293541;
  background: #141c26;
}

.phase-info {
  gap: 13px;
  min-width: 0;
}

.phase-indicator {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1px;
}

.ban-phase {
  color: #e6a4a4;
}

.pick-phase {
  color: #9dc9ae;
}

.phase-dot {
  width: 7px;
  height: 7px;
  flex-shrink: 0;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 9px currentColor;
}

.toolbar-divider {
  width: 1px;
  height: 17px;
  flex-shrink: 0;
  background: #36414e;
}

.turn-label {
  color: #d4dce5;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
}

.muted {
  color: #738194;
}

.map-legend {
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 14px;
  color: #aab5c2;
  font-size: 10px;
}

.map-legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.legend-dot {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  border-radius: 2px;
}

.available {
  background: #f6c418;
}

.banned {
  background: repeating-linear-gradient(
    135deg,
    #a9afb7 0 2px,
    #535d68 2px 4px
  );
}

.legend-dot.picked {
  background-color: #626c77;
  background-image: repeating-linear-gradient(
    -45deg,
    transparent 0px,
    transparent 4px,
    rgba(0, 0, 0, 0.85) 4px,
    rgba(0, 0, 0, 0.85) 6px
  );
  border: 1px solid rgba(0, 0, 0, 0.35);
  border-radius: 2px;
}

/* Obszar mapy */

.map-stage {
  position: relative;
  display: flex;
  flex: 1 1 0;
  min-width: 0;
  min-height: 0;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background:
    radial-gradient(
      ellipse at center,
      rgba(37, 64, 79, 0.42),
      transparent 70%
    ),
    #101c27;
}

.map-background-glow {
  position: absolute;
  width: 80%;
  height: 60%;
  border-radius: 50%;
  background: #33566b;
  filter: blur(90px);
  opacity: 0.08;
  pointer-events: none;
}

/*
 * SVG zachowuje własny viewBox.
 * Nie zmieniamy kadru mapy ani współrzędnych prowincji.
 */
.world-map-container {
  position: relative;
  z-index: 1;
  display: flex;
  flex: 1 1 0;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.world-map-container :global(svg.world-map-svg) {
  display: block;
  flex: 0 1 auto;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  max-width: 100%;
  max-height: 100%;
}

/* Interakcje z prowincjami */

.world-map-container :global(path.interactive-province) {
  cursor: pointer;
  transition: filter 120ms ease, stroke-width 120ms ease;
}

.world-map-container :global(path.interactive-province.country-hovered) {
  filter: brightness(1.12) drop-shadow(0 0 2px rgba(255, 255, 255, 0.65));
  stroke: #263442;
  stroke-width: 1.4;
}

/* Państwo zbanowane: ukośne szare paski */

.world-map-container :global(path.interactive-province.country-banned) {
  fill: url(#draftout-ban-pattern) !important;
  stroke: #454e58;
  stroke-width: 0.8;
  filter: none;
  cursor: not-allowed !important;
}

/* Nakładka zaznaczonego państwa */

.world-map-container :global(path.picked-overlay) {
  pointer-events: none;
}

/* Wybrane państwa nie sugerują możliwości ponownego kliknięcia */

.world-map-container :global(path.interactive-province.country-picked) {
  cursor: not-allowed !important;
}

/* Komunikaty mapy */

.map-message {
  position: relative;
  z-index: 2;
  padding: 14px 18px;
  border: 1px solid #344858;
  border-radius: 5px;
  background: #141c26;
  color: #cbd6e2;
}

.map-message.error {
  color: #e6a4a4;
}

/* Etykiety nakładane na mapę */

.map-overlay-top,
.map-overlay-bottom {
  position: absolute;
  z-index: 2;
  right: 14px;
  left: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  pointer-events: none;
}

.map-overlay-top {
  top: 13px;
}

.map-overlay-bottom {
  bottom: 13px;
}

.map-version,
.map-scale {
  color: #8598a9;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1.5px;
}

.map-version {
  padding: 5px 8px;
  border: 1px solid #344858;
  border-radius: 3px;
  background: rgba(11, 20, 29, 0.85);
  color: #d1dbe4;
}

.map-hint {
  color: #77899a;
  font-size: 9.4px;
}

kbd {
  margin-right: 6px;
  padding: 3px 5px;
  border: 1px solid #354656;
  border-radius: 3px;
  color: #b6c4d1;
  font-size: 9px;
}

/* Pasek akcji pod mapą */

.action-bar {
  display: flex;
  min-height: 76px;
  flex-shrink: 0;
  align-items: center;
  gap: 22px;
  padding: 12px 17px;
  border-top: 1px solid #293541;
  background: #141c26;
}

.turn-player {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: 10px;
}

.turn-avatar {
  display: grid;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  place-items: center;
  border: 1px solid #6688aa;
  border-radius: 5px;
  background: #243a50;
  color: #d9eaff;
  font-size: 14px;
  font-weight: 700;
}

.turn-player > div:last-child {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.turn-player strong {
  color: #eef3f8;
  font-size: 12px;
}

.action-description {
  display: flex;
  flex: 1 1 0;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
  text-align: right;
}

.action-description strong {
  color: #e1e8ef;
  font-size: 12px;
}

.action-description span {
  color: #8391a0;
  font-size: 10px;
}

.demo-button {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid #41566b;
  border-radius: 4px;
  background: #24384b;
  color: #e0ebf5;
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
  transition: background 150ms ease, border-color 150ms ease;
}

.demo-button:hover {
  border-color: #6b8aa7;
  background: #304b64;
}

.demo-button span {
  font-size: 15px;
}

/* Panel graczy */

.players-heading {
  display: flex;
  min-height: 70px;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 13px 13px 12px;
  border-bottom: 1px solid #293541;
  background: #141c26;
}

.players-heading h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 5px 0 0;
  color: #e7edf4;
  font-size: 16px;
  font-weight: 650;
}

.player-count {
  display: grid;
  width: 21px;
  height: 21px;
  flex-shrink: 0;
  place-items: center;
  border: 1px solid #3b4b5d;
  border-radius: 4px;
  color: #a8b8c9;
  font-size: 10px;
}

.order-label {
  gap: 5px;
  color: #788a9d;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.order-label svg {
  width: 13px;
  height: 13px;
  flex-shrink: 0;
}

/* Lista graczy przewija się wewnątrz panelu */

.players-list {
  display: flex;
  flex: 1 1 0;
  min-width: 0;
  min-height: 0;
  flex-direction: column;
  gap: 7px;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 10px;
  overscroll-behavior: contain;
}

.player-card {
  display: flex;
  min-height: 88px;
  flex-shrink: 0;
  align-items: stretch;
  gap: 10px;
  padding: 11px 9px;
  border: 1px solid #2b3744;
  border-radius: 5px;
  background: #141c25;
  transition: border-color 150ms ease, background 150ms ease;
}

.player-card.active {
  border-color: #628bb1;
  background: linear-gradient(105deg, #203449, #17232f);
  box-shadow: inset 3px 0 #86b7e5;
}

.player-number {
  display: grid;
  width: 25px;
  height: 25px;
  flex-shrink: 0;
  place-items: center;
  border: 1px solid #354352;
  border-radius: 4px;
  background: #1b2530;
  color: #a8b7c7;
  font-size: 10px;
  font-weight: 700;
}

.active .player-number {
  border-color: #628bb1;
  background: #2c4863;
  color: #f0f7ff;
}

.player-main {
  display: flex;
  flex: 1 1 0;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
}

.player-name-row {
  display: flex;
  min-height: 17px;
  align-items: center;
  justify-content: space-between;
  gap: 5px;
}

.player-name {
  overflow: hidden;
  color: #e3eaf2;
  font-size: 12px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.current-indicator {
  flex-shrink: 0;
  color: #91bfe8;
  font-size: 7px;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.player-result {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr);
  align-items: baseline;
  gap: 6px;
}

.result-label {
  font-size: 8px;
  letter-spacing: 0.8px;
}

.result-value {
  overflow: hidden;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ban-value {
  color: #dba4a4;
}

.country-value {
  color: #c7d7b5;
}

.result-value.empty {
  color: #647384;
}

.player-status {
  display: flex;
  flex-shrink: 0;
  align-items: flex-start;
}

.status-check,
.status-ban {
  display: grid;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 800;
}

.status-check {
  background: #243e32;
  color: #8ed1a8;
}

.status-ban {
  background: #452a2d;
  color: #e1a1a1;
  font-size: 9px;
}

.status-wait {
  color: #617183;
  font-size: 20px;
  line-height: 18px;
}

/* Stopka panelu graczy */

.players-footer {
  display: flex;
  min-height: 37px;
  flex-shrink: 0;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border-top: 1px solid #293541;
  color: #7c8b9b;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.7px;
}

.footer-dot {
  width: 5px;
  height: 5px;
  background: #799ab9;
}

/* Stopka aplikacji */

.app-footer {
  display: flex;
  min-height: 32px;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 22px;
  border-top: 1px solid #222d38;
  color: #8b99a8;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 1px;
}

.footer-muted {
  color: #536273;
  font-weight: 500;
}

/* Szerokie ekrany */

@media (min-width: 1500px) {
  .main-layout {
    grid-template-columns: minmax(0, 1fr) 310px;
    gap: 18px;
    padding: 22px 24px 14px;
  }

  .players-list {
    gap: 9px;
    padding: 12px;
  }

  .player-card {
    min-height: 92px;
    padding: 12px;
  }
}

/* Niskie okna: zmniejszamy odstępy, nie wymuszamy wysokości mapy */

@media (max-height: 800px) {
  .main-layout {
    padding: 10px 14px 8px;
    gap: 10px;
  }

  .map-toolbar {
    min-height: 40px;
    gap: 8px;
    padding-right: 10px;
    padding-left: 10px;
  }

  .map-legend {
    gap: 8px;
  }

  .action-bar {
    min-height: 62px;
    gap: 14px;
    padding: 8px 12px;
  }

  .players-heading {
    min-height: 58px;
    padding: 8px 12px;
  }

  .players-list {
    gap: 5px;
    padding: 7px;
  }

  .player-card {
    min-height: 76px;
    padding: 8px;
  }

  .players-footer {
    min-height: 30px;
  }
}

.map-reset-button {
  padding: 6px 9px;
  border: 1px solid #344858;
  border-radius: 4px;
  background: rgba(11, 20, 29, 0.9);
  color: #cbd6e2;
  font-size: 10px;
  cursor: pointer;
  pointer-events: auto;
}

.map-reset-button:hover {
  border-color: #7897b4;
  background: #24384b;
}


.confirm-backdrop {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(3px);
}

.confirm-dialog {
  width: 100%;
  max-width: 420px;
  padding: 24px;
  border: 1px solid #3b4655;
  border-radius: 14px;
  background: #151b24;
  color: #e8edf5;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
}

.confirm-dialog h2 {
  margin: 0 0 16px;
  font-size: 21px;
}

.confirm-dialog p {
  line-height: 1.6;
}

.confirm-player {
  color: #9caabd;
  font-size: 14px;
}

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
}

.confirm-actions button {
  padding: 10px 15px;
  border: 1px solid transparent;
  border-radius: 8px;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.confirm-cancel {
  background: #293241;
  color: #e8edf5;
}

.confirm-cancel:hover {
  background: #374356;
}

.confirm-accept {
  background: #2563eb;
  color: white;
}

.confirm-accept:hover {
  background: #1d4ed8;
}

.legend-picked-swatch {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  display: inline-block;
}


.results-backdrop {
  position: fixed;
  inset: 0;
  z-index: 11000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
  background: rgba(3, 7, 12, 0.82);
  backdrop-filter: blur(7px);
}

.results-dialog {
  display: flex;
  width: 100%;
  max-width: 1050px;
  max-height: 90vh;
  max-height: 90dvh;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #39495a;
  border-radius: 12px;
  background:
    radial-gradient(ellipse at 50% 0%, #203247 0%, transparent 55%),
    #101720;
  color: #e8edf5;
  box-shadow: 0 28px 100px rgba(0, 0, 0, 0.65);
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 32px 24px;
  border-bottom: 1px solid #2b3948;
}

.results-header h2 {
  margin: 8px 0;
  color: #f2f6fb;
  font-size: clamp(24px, 3vw, 34px);
  letter-spacing: -0.7px;
}

.results-header p {
  margin: 0;
  color: #93a3b5;
  font-size: 13px;
}

.results-complete {
  flex-shrink: 0;
  padding: 8px 11px;
  border: 1px solid #38654d;
  border-radius: 5px;
  background: #193326;
  color: #9cdbb3;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 1px;
}

.results-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  padding: 20px 32px;
}

.results-stat {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 15px 17px;
  border: 1px solid #2d3b4a;
  border-radius: 7px;
  background: rgba(25, 36, 48, 0.8);
}

.results-stat span {
  color: #899bad;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1px;
}

.results-stat strong {
  color: #f0f5fa;
  font-size: 25px;
}

.results-table-wrapper {
  min-height: 0;
  overflow: auto;
  padding: 0 32px 20px;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.results-table th {
  padding: 13px 14px;
  border-bottom: 1px solid #3a4858;
  color: #8496a9;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.results-table td {
  padding: 16px 14px;
  border-bottom: 1px solid #263340;
  font-size: 12px;
}

.results-table tbody tr {
  background: rgba(20, 29, 39, 0.55);
}

.results-table tbody tr:nth-child(even) {
  background: rgba(29, 41, 54, 0.55);
}

.results-table tbody tr:last-child td {
  border-bottom: none;
}

.results-number {
  width: 45px;
  color: #8294a7;
  font-size: 10px !important;
  font-weight: 700;
}

.results-player {
  color: #e7edf5;
  font-weight: 700;
}

.results-country {
  color: #c7d7b5;
  font-weight: 700;
}

.results-ban {
  color: #dba4a4;
}

.results-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 32px;
  border-top: 1px solid #2b3948;
  background: rgba(11, 16, 23, 0.7);
}

.results-actions button {
  padding: 11px 17px;
  border: 1px solid #405166;
  border-radius: 5px;
  font: inherit;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: background 150ms ease, border-color 150ms ease;
}

.results-close {
  background: #202c39;
  color: #e0e9f2;
}

.results-close:hover {
  border-color: #71869c;
  background: #2b3c4e;
}

.results-reset {
  border-color: #526f8b !important;
  background: #29435b;
  color: #f0f6fc;
}

.results-reset:hover {
  border-color: #83a6c7 !important;
  background: #365874;
}

@media (max-width: 760px) {
  .results-backdrop {
    padding: 12px;
  }

  .results-header {
    align-items: flex-start;
    flex-direction: column;
    padding: 22px;
  }

  .results-summary {
    gap: 8px;
    padding: 14px 22px;
  }

  .results-stat {
    padding: 12px;
  }

  .results-stat strong {
    font-size: 20px;
  }

  .results-table-wrapper {
    padding: 0 12px 14px;
  }

  .results-table th,
  .results-table td {
    padding: 12px 9px;
  }

  .results-actions {
    padding: 16px 22px;
  }
}


.draft-paused-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(12, 17, 23, 0.58);
  backdrop-filter: grayscale(1) blur(1.5px);
  -webkit-backdrop-filter: grayscale(1) blur(1.5px);
  cursor: not-allowed;
}

.draft-paused-content {
  max-width: 100%;
  text-align: center;
  pointer-events: none;
}

.draft-paused-icon {
  display: grid;
  width: 48px;
  height: 48px;
  margin: 0 auto 18px;
  place-items: center;
  border: 1px solid rgba(197, 210, 223, 0.35);
  border-radius: 50%;
  background: rgba(18, 27, 37, 0.85);
  color: #d6dee7;
  font-size: 23px;
  font-weight: 800;
}

.draft-paused-content h2 {
  margin: 0;
  color: #f1f4f8;
  font-size: clamp(24px, 3vw, 38px);
  font-weight: 800;
  letter-spacing: -0.7px;
  text-shadow: 0 2px 14px rgba(0, 0, 0, 0.6);
}

.draft-paused-content p {
  margin: 12px 0 0;
  color: #d0d8e1;
  font-size: 14px;
  letter-spacing: 0.4px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.8);
}

.map-stage:has(.draft-paused-overlay) .world-map-container {
  filter: grayscale(0.8);
}

</style>
