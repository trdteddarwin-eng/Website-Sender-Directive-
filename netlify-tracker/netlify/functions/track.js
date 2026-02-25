// Email open tracking pixel — returns 1x1 transparent GIF and increments open_count in Supabase.

const PIXEL = Buffer.from(
  "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
  "base64"
);

const headers = {
  "Content-Type": "image/gif",
  "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
  "Pragma": "no-cache",
};

exports.handler = async (event) => {
  const emailId = event.queryStringParameters?.t;

  if (emailId) {
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_KEY;

    if (supabaseUrl && supabaseKey) {
      try {
        // Fetch current open_count
        const getRes = await fetch(
          `${supabaseUrl}/rest/v1/emails?id=eq.${emailId}&select=open_count`,
          {
            headers: {
              apikey: supabaseKey,
              Authorization: `Bearer ${supabaseKey}`,
            },
          }
        );
        const rows = await getRes.json();
        const currentCount = rows?.[0]?.open_count || 0;

        // Increment open_count and set last_opened_at
        await fetch(
          `${supabaseUrl}/rest/v1/emails?id=eq.${emailId}`,
          {
            method: "PATCH",
            headers: {
              apikey: supabaseKey,
              Authorization: `Bearer ${supabaseKey}`,
              "Content-Type": "application/json",
              Prefer: "return=minimal",
            },
            body: JSON.stringify({
              open_count: currentCount + 1,
              last_opened_at: new Date().toISOString(),
            }),
          }
        );
      } catch (err) {
        // Silently fail — never break email rendering
        console.error("Tracking error:", err.message);
      }
    }
  }

  return { statusCode: 200, headers, body: PIXEL.toString("base64"), isBase64Encoded: true };
};
