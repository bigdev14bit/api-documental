package example;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping(path = "/api/")
public class UserController {
    @GetMapping("/health")
    public String health() {
        return "ok";
    }

    @PostMapping(path = "/users")
    public void createUser() {}

    @PutMapping(value = "/users/{id}")
    public void updateUser() {}

    @PatchMapping("/users/{id}")
    public void patchUser() {}

    @DeleteMapping("/users/{id}")
    public void deleteUser() {}

    @RequestMapping(value = "/users/{id}", method = RequestMethod.GET)
    public String getUser() {
        return "user";
    }

    @RequestMapping(
        path = {"/items", "/things"},
        method = {RequestMethod.POST, RequestMethod.PUT}
    )
    public void createItem() {}

    @GetMapping
    public void root() {}

    @GetMapping(path = dynamicPath)
    public void dynamicPath() {}

    @GetMapping("/users/" + userId)
    public void concatenatedPath() {}

    @RequestMapping("/unknown-method")
    public void unknownMethod() {}

    @RequestMapping(path = "/unsupported", method = String.valueOf("GET"))
    public void unsupportedMethod() {}

    private final String example = "@GetMapping(\"/inside-a-string\")";

    // @DeleteMapping("/commented-out")
    /* @PostMapping("/also-commented-out") */
    public void examples() {}

    @RestController
    @RequestMapping("/admin")
    static class AdminController {
        @GetMapping("/users")
        public void listUsers() {}
    }
}

@RequestMapping(path = "/restricted", method = RequestMethod.GET)
class RestrictedController {
    @RequestMapping
    public void getRoot() {}
}

@RequestMapping(path = API_PREFIX)
class DynamicPrefixController {
    @GetMapping("/hidden")
    public void hidden() {}
}
