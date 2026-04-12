export function resourceLinkForAction(action: string): string {
  const query = action.toLowerCase();

  if (query.includes("kubernetes") || query.includes("distributed")) {
    return "https://kubernetes.io/docs/tutorials/";
  }
  if (query.includes("pytorch") || query.includes("deep learning")) {
    return "https://pytorch.org/tutorials/";
  }
  if (query.includes("aws") || query.includes("cloud")) {
    return "https://aws.amazon.com/training/";
  }
  if (query.includes("sql") || query.includes("database")) {
    return "https://www.postgresql.org/docs/current/tutorial-sql.html";
  }

  return `https://www.google.com/search?q=${encodeURIComponent(action + " internship learning path")}`;
}