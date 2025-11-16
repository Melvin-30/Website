export async function handler(event, context) {
  const page = event.queryStringParameters.page;

  const files = {
    "SOP1": "https://myprojectwork.free.nf/SOP1.php",
    "SOP2": "https://myprojectwork.free.nf/SOP2.php",
    "SOP4": "https://myprojectwork.free.nf/SOP4.php",
    "SOP5": "https://myprojectwork.free.nf/SOP5.php",
    "SOP6": "https://myprojectwork.free.nf/SOP6.php"
  };

  if (!files[page]) {
    return {
      statusCode: 400,
      body: "Invalid or missing page parameter."
    };
  }

  try {
    const response = await fetch(files[page]);
    const html = await response.text();

    return {
      statusCode: 200,
      headers: { "Content-Type": "text/html" },
      body: html
    };

  } catch (err) {
    return {
      statusCode: 500,
      body: "Error loading PHP file: " + err.toString()
    };
  }
}
