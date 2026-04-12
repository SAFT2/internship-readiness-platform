import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section className="not-found">
      <div className="card soft-card center">
        <h1>404</h1>
        <p>Oops! Page not found</p>
        <Link to="/" className="btn btn-primary">
          Return to Home
        </Link>
      </div>
    </section>
  );
}
