<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { supabase } from '../../lib/supabaseClient';

  let pauseBusy = $state(false);
  let roomPaused = $state(false);

  let checking = $state(true);
  let authorized = $state(false);
  let busy = $state(false);
  let message = $state('');

  let roomCode = $state('');
  let playerNames = $state(
    'Janek\nDominik\nKonrad\nSkraba\nRafał\nMati\nJasiek\nKrzysiek\nPiotrek\nKarol'
  );

  let createdRoomCode = $state('');

type PlayerAccessLink = {
  seat: number;
  name: string;
  url: string;
};

let issuedLinks = $state<PlayerAccessLink[]>([]);

  onMount(async () => {
    const {
      data: { session }
    } = await supabase.auth.getSession();

    if (!session) {
      await goto('/login');
      return;
    }

    const { data, error } = await supabase.rpc('is_draft_admin');

    if (error || data !== true) {
      message = error
        ? `Nie udało się sprawdzić uprawnień: ${error.message}`
        : 'To konto nie ma uprawnień administratora.';

      checking = false;
      return;
    }

    authorized = true;
    checking = false;
  });

  async function logout() {
    const { error } = await supabase.auth.signOut();

    if (error) {
      message = `Nie udało się wylogować: ${error.message}`;
      return;
    }

    await goto('/login');
  }

  async function createRoom(event: SubmitEvent) {
    event.preventDefault();

    if (busy || !authorized) return;

    const names = playerNames
      .split('\n')
      .map((name) => name.trim())
      .filter(Boolean);

    const code = roomCode.trim().toUpperCase();

    if (code.length < 4 || code.length > 32) {
      message = 'Kod pokoju musi mieć od 4 do 32 znaków.';
      return;
    }

    if (names.length < 2 || names.length > 16) {
      message = 'Podaj od 2 do 16 graczy.';
      return;
    }

    busy = true;
    message = '';

    try {
      const { data, error } = await supabase.rpc(
        'create_draft_room',
        {
          p_code: code,
          p_player_names: names
        }
      );

      if (error) throw error;

      if (!data) {
        throw new Error('Baza nie zwróciła utworzonego pokoju.');
      }

      createdRoomCode = code;
await generatePlayerLinks(code);
message = `Pokój ${code} został utworzony. Linki graczy wygenerowano.`;
    } catch (error) {
      message =
        error instanceof Error
          ? error.message
          : 'Nie udało się utworzyć pokoju.';
    } finally {
      busy = false;
    }
  }

  async function resetRoom() {
    if (busy || !authorized) return;

    const code = roomCode.trim().toUpperCase();

    if (!code) {
      message = 'Wpisz kod pokoju, który chcesz zresetować.';
      return;
    }

    if (!confirm(`Czy na pewno zresetować draft ${code}?`)) return;

    busy = true;
    message = '';

    try {
      const { error } = await supabase.rpc('reset_draft_room', {
        p_code: code
      });

      if (error) throw error;

      message = `Draft ${code} został zresetowany.`;
    } catch (error) {
      message =
        error instanceof Error
          ? error.message
          : 'Nie udało się zresetować draftu.';
    } finally {
      busy = false;
    }
  }


async function toggleRoomPause() {
  if (busy || pauseBusy || !authorized) return;

  const code = roomCode.trim().toUpperCase();

  if (!code) {
    message = 'Wpisz kod pokoju, który chcesz zapauzować lub wznowić.';
    return;
  }

  pauseBusy = true;
  message = '';

  const { data: roomData, error: roomError } = await supabase.rpc(
  'get_draft_room',
  { p_code: code }
);

if (roomError) throw roomError;
if (!roomData) throw new Error('Nie znaleziono pokoju.');

const nextPausedState =
  !(roomData as { is_paused: boolean }).is_paused;

  try {
    const { data, error } = await supabase.rpc('set_draft_paused', {
      p_code: code,
      p_paused: nextPausedState
    });

    if (error) throw error;

    roomPaused = data === true;
    message = roomPaused
      ? `Draft ${code} został zapauzowany.`
      : `Draft ${code} został wznowiony.`;
  } catch (error) {
    message =
      error instanceof Error
        ? error.message
        : 'Nie udało się zmienić stanu pauzy.';
  } finally {
    pauseBusy = false;
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

  issuedLinks = result.players.map((player) => ({
    seat: player.seat,
    name: player.name,
    url:
      `${window.location.origin}/?room=${encodeURIComponent(result.code)}` +
      `#token=${player.token}`
  }));
}

async function copyPlayerLink(url: string) {
  try {
    await navigator.clipboard.writeText(url);
    alert('Link skopiowany do schowka!');
  } catch (error) {
    console.error('Błąd kopiowania linku:', error);
    alert('Nie udało się skopiować linku. Skopiuj go ręcznie z pola obok.');
  }
}
</script>

<svelte:head>
  <title>Organizator</title>
</svelte:head>

<main class="admin-layout admin-page">
  <header>
    <a href="/" class="brand">DRAFTOUT</a>

    {#if authorized}
      <button class="secondary" onclick={logout}>Wyloguj</button>
    {/if}
  </header>

  {#if checking}
    <p>Sprawdzanie sesji i uprawnień…</p>
  {:else if authorized}
    <p class="eyebrow">PANEL ORGANIZATORA</p>
    <h1>Zarządzanie draftem</h1>
    <p class="muted">
      Twórz pokoje turniejowe i zarządzaj ich stanem.
    </p>

    <section class="panel">
      <h2>Nowy pokój</h2>

      <form onsubmit={createRoom}>
        <label for="code">Kod pokoju</label>
        <input
          id="code"
          bind:value={roomCode}
          placeholder="np. ALPHA-7"
          minlength="4"
          maxlength="32"
          required
        />

        <label for="names">Lista graczy: jeden gracz w każdym wierszu</label>
        <textarea
          id="names"
          bind:value={playerNames}
          rows="9"
          required
        ></textarea>

        <button type="submit" disabled={busy}>
          {busy ? 'Przetwarzanie…' : 'Utwórz pokój'}
        </button>
      </form>
    </section>

    <section class="panel">
      <h2>Reset draftu</h2>
      <p class="muted">
        Usuwa bany i wybory w podanym pokoju oraz rozpoczyna draft od początku.
      </p>

      <button
        class="danger"
        onclick={resetRoom}
        disabled={busy}
      >
        Resetuj pokój z powyższego kodu
      </button>
    </section>


<section class="panel">
  <h2>Pauza draftu</h2>
  <p class="muted">
    Zatrzymuje wybory na mapie dla wszystkich graczy.
    Wpisz kod pokoju w polu powyżej.
  </p>

  <p>
    Stan:
    <strong>{roomPaused ? 'Zapauzowany' : 'Wznowiony'}</strong>
  </p>

  <button
    class:danger={ !roomPaused }
    onclick={toggleRoomPause}
    disabled={busy || pauseBusy}
  >
    {pauseBusy
      ? 'Zmienianie stanu…'
      : roomPaused
        ? 'Wznów draft'
        : 'Zapauzuj draft'}
  </button>
</section>


    {#if createdRoomCode}
      <section class="panel">
        <h2>Utworzony pokój</h2>
        <p>
          Kod: <strong>{createdRoomCode}</strong>
        </p>
        <a class="room-link" href={`/?room=${encodeURIComponent(createdRoomCode)}`}>
          Otwórz draft
        </a>
      </section>
    {/if}
  {:else}
    <section class="panel">
      <h1>Brak dostępu</h1>
      <p>{message}</p>
      <button onclick={logout}>Wyloguj</button>
    </section>
  {/if}

  {#if message && authorized}
    <p class="message" aria-live="polite">{message}</p>
  {/if}

  {#if issuedLinks.length > 0}
  <section class="access-links">
    <h2>Linki dostępu dla graczy</h2>
    <p>Każdy link przekaż wyłącznie przypisanemu graczowi.</p>

    {#each issuedLinks as player (player.seat)}
      <div class="access-link">
        <strong>
          Miejsce {player.seat + 1}: {player.name}
        </strong>

        <input
          readonly
          value={player.url}
          aria-label={`Link dostępu dla ${player.name}`}
        />

<button
  type="button"
  onclick={() => copyPlayerLink(player.url)}
>
  Kopiuj link
</button>
      </div>
    {/each}
  </section>
{/if}
</main>

<style>
  :global(*) {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    background: #0b0f14;
    color: #e8edf3;
    font-family: Inter, "Segoe UI", Arial, sans-serif;
  }

  .admin-page {
    width: min(900px, 100%);
    margin: 0 auto;
    padding: 30px 22px 60px;
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 45px;
  }

  .brand {
    color: #f1f5f9;
    font-size: 16px;
    font-weight: 800;
    letter-spacing: 3px;
    text-decoration: none;
  }

  .eyebrow {
    color: #8ba8c2;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
  }

  h1 {
    margin: 8px 0;
    font-size: 30px;
  }

  h2 {
    margin-top: 0;
    font-size: 17px;
  }

  .muted {
    color: #9baaba;
    line-height: 1.6;
  }

  .panel {
    margin-top: 22px;
    padding: 24px;
    border: 1px solid #2a3541;
    border-radius: 7px;
    background: #101720;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  label {
    margin-top: 8px;
    color: #cbd5e1;
    font-size: 12px;
  }

  input,
  textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #344252;
    border-radius: 5px;
    background: #0b1118;
    color: #f1f5f9;
    font: inherit;
  }

  textarea {
    resize: vertical;
  }

  button,
  .room-link {
    display: inline-block;
    width: fit-content;
    padding: 11px 15px;
    border: 1px solid #526f8b;
    border-radius: 5px;
    background: #29435b;
    color: white;
    font: inherit;
    font-size: 12px;
    font-weight: 700;
    text-decoration: none;
    cursor: pointer;
  }

  button:disabled {
    opacity: 0.6;
    cursor: wait;
  }

  .secondary {
    background: #202c39;
    border-color: #405166;
  }

  .danger {
    background: #492b30;
    border-color: #75434a;
  }

  .message {
    padding: 14px;
    border: 1px solid #344252;
    border-radius: 5px;
    overflow-wrap: anywhere;
  }

  :global(html:has(.admin-page)),
:global(body:has(.admin-page)) {
  overflow-y: scroll !important;
  min-height: 100%;
}

.admin-page {
  min-height: 100vh;
  overflow-y: auto;
  scrollbar-gutter: stable;
}
</style>
