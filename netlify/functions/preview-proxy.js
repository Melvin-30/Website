export async function handler(event, context) {
  const page = event.queryStringParameters?.page;

  // Map SOP pages to HTTPS URLs
  const files = {
    "SOP1": "https://myprojectwork.free.nf/SOP1.php",
    "SOP2": "https://myprojectwork.free.nf/SOP2.php",
    "SOP4": "https://myprojectwork.free.nf/SOP4.php",
    "SOP5": "https://myprojectwork.free.nf/SOP5.php",
    "SOP6": "https://myprojectwork.free.nf/SOP6.php"
  };

  // Validate page
  if (!page || !files[page]) {
    return {
      statusCode: 400,
      body: "Invalid or missing page parameter."
    };
  }

  try {
    // Fetch PHP page from InfinityFree
    const response = await fetch(files[page]);

    if (!response.ok) {
      return {
        statusCode: response.status,
        body: `Failed to fetch PHP page. Status: ${response.status}`
      };
    }

    let html = await response.text();

    // 1. Remove any insecure iframes (like cookies.html)
    html = html.replace(/<iframe[^>]*cookies\.html[^>]*><\/iframe>/gi, '');

    // 2. Rewrite relative URLs so CSS/JS/images still work
    const baseURL = files[page].replace(/\/[^/]*$/, '/'); // base directory
    html = html.replace(/(href|src)="(?!https?:\/\/)([^"]*)"/gi, (match, attr, url) => {
      return `${attr}="${baseURL}${url}"`;
    });

    return {
      statusCode: 200,
      headers: {
        "Content-Type": "text/html",
        "Cache-Control": "no-cache"
      },
      body: html
    };

  } catch (err) {
    return {
      statusCode: 500,
      body: "Error loading PHP file: " + err.toString()
    };
  }
}
