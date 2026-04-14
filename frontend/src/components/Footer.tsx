import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <div>
          <p className="footer-brand">InternReady AI</p>
          <p className="footer-copy">© 2024 InternReady AI. Built for the next generation of engineers.</p>
        </div>
        <div className="footer-links">
          <Link to="#">Privacy Policy</Link>
          <Link to="#">Terms of Service</Link>
          <Link to="#">AI Ethics</Link>
          <Link to="#">Contact Support</Link>
        </div>
      </div>
    </footer>
  );
}
