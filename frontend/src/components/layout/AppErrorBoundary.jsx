import { Component } from "react";

class AppErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    render() {
        if (!this.state.hasError) return this.props.children;

        return <main className="app-recovery" role="alert">
            <span>Match centre recovery</span>
            <h1>That page lost its shape.</h1>
            <p>Your saved clubs and stored data are safe. Reload to reconnect to the latest football data.</p>
            <button type="button" onClick={() => window.location.reload()}>Reload the platform</button>
        </main>;
    }
}

export default AppErrorBoundary;
