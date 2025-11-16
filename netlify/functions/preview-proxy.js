export async function handler(event, context) {
  const page = event.queryStringParameters?.page;

  // Map of SOP pages to PHP URLs
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
    // Fetch the PHP page from InfinityFree
    const response = await fetch(files[page]);

    if (!response.ok) {
      return {
        statusCode: response.status,
        body: `Failed to fetch PHP page. Status: ${response.status}`
      };
    }

    let html = await response.text();

    // Optional: Rewrite relative URLs in HTML so they work in iframe
    html = html.replace(
      /href="(?!https?:\/\/)/g,
      'href="' + files[page].replace(/\/[^/]*$/, '/') // base URL
    ).replace(
      /src="(?!https?:\/\/)/g,
      'src="' + files[page].replace(/\/[^/]*$/, '/')
    );

    return {
      statusCode: 200,
      headers: {
        "Content-Type": "text/html",
        "Cache-Control": "no-cache" // optional, always fetch fresh
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
