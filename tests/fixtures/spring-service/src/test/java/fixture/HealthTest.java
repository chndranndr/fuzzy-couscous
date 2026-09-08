package fixture;

public final class HealthTest {
    public static void main(String[] args) {
        if (!"UP".equals(healthStatus())) {
            throw new AssertionError("health status changed");
        }
    }

    private static String healthStatus() {
        return "UP";
    }
}
