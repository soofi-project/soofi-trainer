var config = {
    publicEdcEndpoint: "http://edc-provider:19291/public",
    title: "EDC Portal - Provider",
    theme: {
        light: {
            palette: {
                primary: { main: "#00897b" },
                secondary: { main: "#4db6ac" },
                background: { default: "#f1f8f6" },
                text: {
                    primary: "#1a2e29",
                    secondary: "#4a5d58"
                }
            },
            logo: {
                sx: {
                    height: 40,
                    width: 40,
                    mask: "url(/logo.svg) no-repeat center / contain",
                    backgroundColor: "#00897b"
                }
            }
        },
        dark: {
            palette: {
                primary: { main: "#26a69a" },
                secondary: { main: "#4db6ac" },
                background: { default: "#0d1f1a", paper: "#1a332c" }
            },
            logo: {
                sx: {
                    height: 40,
                    width: 40,
                    mask: "url(/logo.svg) no-repeat center / contain",
                    backgroundColor: "#26a69a"
                }
            }
        }
    }
}