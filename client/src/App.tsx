import { useAuth } from "@/hooks/use-auth";
import { Route, Switch } from "wouter";
import LoginPage from "@/pages/LoginPage";
import WellListPage from "@/pages/WellListPage";
import WellDetailPage from "@/pages/WellDetailPage";

export default function App() {
  const { user, isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-white sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <h1 className="text-lg font-semibold">Engineering Workbook</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">{user?.username}</span>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Switch>
          <Route path="/" component={WellListPage} />
          <Route path="/wells/:id">
            {(params) => <WellDetailPage wellId={Number(params.id)} />}
          </Route>
        </Switch>
      </main>
    </div>
  );
}
