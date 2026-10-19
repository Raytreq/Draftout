
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { supabase } from '../../lib/supabaseClient';

  let email = $state('');
  let password = $state('');
  let errorMessage = $state('');
  let loading = $state(false);

  onMount(async () => {
    const { data } = await supabase.auth.getSession();

    if (data.session) {
      await goto('/admin');
    }
  });

  async function login(event: SubmitEvent) {
    event.preventDefault();

    if (loading) return;

    loading = true;
    errorMessage = '';

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password
      });

      if (error) throw error;

      await goto('/admin');
    } catch (error) {
      errorMessage =
        error instanceof Error
          ? error.message
          : 'Nie udało się zalogować.';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Logowanie</title>
</svelte:head>

<main class="login-page">
  <form class="login-card" onsubmit={login}>
    <a class="brand" href="/">DRAFTOUT</a>

    <p class="eyebrow">PANEL ORGANIZATORA</p>
    <h1>Logowanie</h1>
    <p class="description">
      Zaloguj się na konto organizatora turnieju.
    </p>

    <label for="email">Adres e-mail</label>
    <input
      id="email"
      type="email"
      bind:value={email}
      autocomplete="username"
      required
    />

    <label for="password">Hasło</label>
    <input
      id="password"
      type="password"
      bind:value={password}
      autocomplete="current-password"
      required
    />

    {#if errorMessage}
      <p class="error">{errorMessage}</p>
    {/if}

    <button type="submit" disabled={loading}>
      {loading ? 'Logowanie…' : 'Zaloguj się'}
    </button>

    <a class="back" href="/">Powrót do draftu</a>
  </form>
</main>

<style>
  :global(*) {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    min-height: 100vh;
    background: #0b0f14;
    color: #e8edf3;
    font-family: Inter, "Segoe UI", Arial, sans-serif;
  }

  .login-page {
    min-height: 100vh;
    display: grid;
    place-items: center;
    padding: 24px;
    background: radial-gradient(ellipse at top, #1b2c3d, #0b0f14 65%);
  }

  .login-card {
    width: 100%;
    max-width: 410px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 32px;
    border: 1px solid #2a3541;
    border-radius: 9px;
    background: #101720;
  }

  .brand {
    margin-bottom: 22px;
    color: #f1f5f9;
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 3px;
    text-decoration: none;
  }

  .eyebrow {
    margin: 0;
    color: #8ba8c2;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
  }

  h1 {
    margin: 0;
    font-size: 28px;
  }

  .description {
    margin: 0 0 12px;
    color: #9baaba;
    line-height: 1.5;
  }

  label {
    margin-top: 5px;
    color: #cbd5e1;
    font-size: 12px;
  }

  input {
    width: 100%;
    padding: 12px;
    border: 1px solid #344252;
    border-radius: 5px;
    background: #0b1118;
    color: #f1f5f9;
    font: inherit;
  }

  input:focus {
    outline: 1px solid #719bc0;
    border-color: #719bc0;
  }

  button {
    margin-top: 10px;
    padding: 12px;
    border: 1px solid #526f8b;
    border-radius: 5px;
    background: #29435b;
    color: white;
    font: inherit;
    font-weight: 700;
    cursor: pointer;
  }

  button:disabled {
    opacity: 0.6;
    cursor: wait;
  }

  .error {
    margin: 4px 0;
    color: #f0a3a3;
    overflow-wrap: anywhere;
  }

  .back {
    margin-top: 8px;
    color: #9baaba;
    font-size: 12px;
    text-align: center;
    text-decoration: none;
  }
</style>
