var config = {
    publicEdcEndpoint: "http://edc-consumer:19291/public",
    title: "EDC Portal - Consumer",
    theme: {
        light: {
            palette: {
                primary: { main: "#1976d2" },
                secondary: { main: "#42a5f5" },
                background: { default: "#f5f9ff" },
                text: {
                    primary: "#1a1a2e",
                    secondary: "#4a5568"
                }
            },
            logo: {
                sx: {
                    height: 40,
                    width: 40,
                    mask: "url(/logo.svg) no-repeat center / contain",
                    backgroundColor: "#1976d2"
                }
            }
        },
        dark: {
            palette: {
                primary: { main: "#64b5f6" },
                secondary: { main: "#90caf9" },
                background: { default: "#0a1929", paper: "#132f4c" }
            },
            logo: {
                sx: {
                    height: 40,
                    width: 40,
                    mask: "url(/logo.svg) no-repeat center / contain",
                    backgroundColor: "#64b5f6"
                }
            }
        }
    }
}