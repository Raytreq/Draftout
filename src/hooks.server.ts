
import { createServerClient } from '@supabase/ssr';

export const handle = async ({
  event,
  resolve
}: {
  event: import('@sveltejs/kit').RequestEvent;
  resolve: (event: import('@sveltejs/kit').RequestEvent) => Promise<Response>;
}) => {
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
  const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

  if (!supabaseUrl || !supabaseKey) {
    throw new Error(
      'Brak VITE_SUPABASE_URL lub VITE_SUPABASE_PUBLISHABLE_KEY w pliku .env.'
    );
  }

  event.locals.supabase = createServerClient(
    supabaseUrl,
    supabaseKey,
    {
      cookies: {
        getAll: () => event.cookies.getAll(),

        setAll: (cookiesToSet) => {
          cookiesToSet.forEach(({ name, value, options }) => {
            event.cookies.set(name, value, {
              ...options,
              path: '/'
            });
          });
        }
      }
    }
  );

  event.locals.getSession = async () => {
    const {
      data: { user },
      error
    } = await event.locals.supabase.auth.getUser();

    return error ? null : user;
  };

  return resolve(event);
};
