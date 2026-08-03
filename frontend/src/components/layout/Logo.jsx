import "./Logo.css";

function Logo() {
    return (
        <div className="logo-box">

            <div className="logo-title">
                FI
            </div>

            <div className="graph">

                <span className="node node1"></span>

                <span className="line line1"></span>

                <span className="node node2"></span>

                <span className="line line2"></span>

                <span className="node node3"></span>

                <span className="arrow"></span>

            </div>

        </div>
    );
}

export default Logo;