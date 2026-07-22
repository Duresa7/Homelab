# Incorrect and stale endpoint identities

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

My live audit found manager ID `002` `edge-01` and ID `003` `wp-01`, both disconnected. Endpoint inspection proved `app-01` carried the `wp-01` key while `edge-01` carried its matching old key; both configurations still used the manager's retired MGMT-A address.

I stopped and disabled the old endpoint services before clearing their keys. I wrote the new manager address into each configuration, removed the two manager registrations by exact ID, and confirmed the manager then held only local ID `000`. `supabase-01` and `alpha-prod-01` had no installed agent, so I left them unchanged.
