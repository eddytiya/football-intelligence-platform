import AppRoutes from "./routes";
import { ThemeProvider } from "./components/layout/ThemeToggle";

function App() {
    return <ThemeProvider><AppRoutes /></ThemeProvider>;
}

export default App;
