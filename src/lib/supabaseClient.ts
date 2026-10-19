
import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

if (!url || !key) {
  throw new Error(
    'Brak VITE_SUPABASE_URL lub VITE_SUPABASE_PUBLISHABLE_KEY w pliku .env.'
  );
}

export const supabase = createClient(url, key);
