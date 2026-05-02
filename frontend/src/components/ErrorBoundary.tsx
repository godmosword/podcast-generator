import React from "react";

type Props = {
  children: React.ReactNode;
};

type State = {
  hasError: boolean;
};

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    console.error("Application error", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="error-boundary">
          <h1>Application error</h1>
          <p>Please refresh the page.</p>
        </main>
      );
    }

    return this.props.children;
  }
}
