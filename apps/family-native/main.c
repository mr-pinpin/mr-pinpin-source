/* Native Atlas pilot. Owned functional code: MIT; illustrations retain
 * CONTENT-LICENSE.md. */
#include <GLES2/gl2.h>
#include <SDL2/SDL.h>
#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static GLuint program, vbo, white;
static GLint attr, uvattr, tint;
static float W = 1920, H = 1080;
static float clamp(float x, float a, float b) { return fmaxf(a, fminf(b, x)); }
static void viewport(SDL_Window *window) {
  int width, height, drawable_width, drawable_height;
  SDL_GetWindowSize(window, &width, &height);
  SDL_GL_GetDrawableSize(window, &drawable_width, &drawable_height);
  if (width > 0 && height > 0) {
    W = (float)width;
    H = (float)height;
  }
  glViewport(0, 0, drawable_width, drawable_height);
}
static GLuint shader(GLenum type, const char *text) {
  GLuint s = glCreateShader(type);
  GLint ok;
  glShaderSource(s, 1, &text, NULL);
  glCompileShader(s);
  glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
  if (!ok) {
    char b[1024];
    glGetShaderInfoLog(s, sizeof b, NULL, b);
    fprintf(stderr, "shader: %s\n", b);
    exit(2);
  }
  return s;
}
static GLuint texture(const char *path, int w, int h) {
  size_t n = (size_t)w * h * 4;
  unsigned char *p = malloc(n);
  FILE *f = fopen(path, "rb");
  if (!p || !f || fread(p, 1, n, f) != n) {
    fprintf(stderr, "asset unavailable: %s\n", path);
    exit(3);
  }
  if (fgetc(f) != EOF) {
    fprintf(stderr, "asset size mismatch: %s\n", path);
    exit(3);
  }
  fclose(f);
  GLuint t;
  glGenTextures(1, &t);
  glBindTexture(GL_TEXTURE_2D, t);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
  glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE,
               p);
  free(p);
  return t;
}
static void quad(GLuint tex, float x, float y, float w, float h, float u,
                 float v, float uw, float vh, float r, float g, float b,
                 float a) {
  float l = x / W * 2 - 1, rr = (x + w) / W * 2 - 1, top = 1 - y / H * 2,
        bot = 1 - (y + h) / H * 2;
  float z[] = {l, top, u, v,      rr, top, u + uw, v,
               l, bot, u, v + vh, rr, bot, u + uw, v + vh};
  glBindTexture(GL_TEXTURE_2D, tex);
  glUniform4f(tint, r, g, b, a);
  glBindBuffer(GL_ARRAY_BUFFER, vbo);
  glBufferData(GL_ARRAY_BUFFER, sizeof z, z, GL_STREAM_DRAW);
  glVertexAttribPointer((GLuint)attr, 2, GL_FLOAT, 0, 4 * sizeof(float),
                        (void *)0);
  glVertexAttribPointer((GLuint)uvattr, 2, GL_FLOAT, 0, 4 * sizeof(float),
                        (void *)(2 * sizeof(float)));
  glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
}
int main(void) {
  char executable[PATH_MAX];
  ssize_t n = readlink("/proc/self/exe", executable, sizeof executable - 1);
  if (n > 0) {
    executable[n] = 0;
    char *slash = strrchr(executable, '/');
    if (slash) {
      *slash = 0;
      if (chdir(executable)) {
        perror("chdir");
        return 1;
      }
    }
  }
  setenv("SDL_WEBOS_ACCESS_POLICY_KEYS_BACK", "true", 1);
  SDL_SetHint("SDL_VIDEO_ALLOW_SCREENSAVER", "0");
  if (SDL_Init(SDL_INIT_VIDEO)) {
    fprintf(stderr, "SDL: %s\n", SDL_GetError());
    return 1;
  }
  SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_ES);
  SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2);
  SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0);
  SDL_GL_SetAttribute(SDL_GL_RED_SIZE, 8);
  SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 8);
  SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, 8);
  SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, 8);
  SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 0);
  SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 0);
  SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
  SDL_Window *window = SDL_CreateWindow("family-native", 0, 0, (int)W, (int)H,
                                        SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN |
                                            SDL_WINDOW_BORDERLESS);
  if (!window) {
    fprintf(stderr, "window: %s\n", SDL_GetError());
    return 1;
  }
  SDL_GLContext context = SDL_GL_CreateContext(window);
  if (!context) {
    fprintf(stderr, "GL: %s\n", SDL_GetError());
    return 1;
  }
  SDL_GL_SetSwapInterval(1);
  const char *vs = "attribute vec2 p;attribute vec2 uv;varying vec2 t;void "
                   "main(){t=uv;gl_Position=vec4(p,0.,1.);}";
  const char *fs =
      "precision mediump float;varying vec2 t;uniform sampler2D image;uniform "
      "vec4 color;void main(){gl_FragColor=texture2D(image,t)*color;}";
  GLuint vertex = shader(GL_VERTEX_SHADER, vs),
         fragment = shader(GL_FRAGMENT_SHADER, fs);
  program = glCreateProgram();
  glAttachShader(program, vertex);
  glAttachShader(program, fragment);
  glLinkProgram(program);
  GLint ok;
  glGetProgramiv(program, GL_LINK_STATUS, &ok);
  if (!ok) {
    char b[1024];
    glGetProgramInfoLog(program, sizeof b, NULL, b);
    fprintf(stderr, "link: %s\n", b);
    return 2;
  }
  glUseProgram(program);
  attr = glGetAttribLocation(program, "p");
  uvattr = glGetAttribLocation(program, "uv");
  tint = glGetUniformLocation(program, "color");
  glUniform1i(glGetUniformLocation(program, "image"), 0);
  glGenBuffers(1, &vbo);
  glEnableVertexAttribArray((GLuint)attr);
  glEnableVertexAttribArray((GLuint)uvattr);
  glEnable(GL_BLEND);
  glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
  viewport(window);
  GLuint map = texture("assets/map.rgba", 1536, 1024), walk[8];
  for (int i = 0; i < 8; i++) {
    char p[80];
    snprintf(p, sizeof p, "assets/walk%03d.rgba", i * 45);
    walk[i] = texture(p, 1440, 540);
  }
  unsigned char pixel[] = {255, 255, 255, 255};
  glGenTextures(1, &white);
  glBindTexture(GL_TEXTURE_2D, white);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
  glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 1, 1, 0, GL_RGBA, GL_UNSIGNED_BYTE,
               pixel);
  float px = 768, py = 650, tx = 768, ty = 650, cx = 768, cy = 512, zoom = 1.5f,
        cursorx = W / 2, cursory = H / 2;
  int running = 1, active = 1, direction = 0, frame = 0;
  float animation = 0;
  uint64_t last = SDL_GetPerformanceCounter(), frames = 0;
  double elapsed = 0, report = 0;
  fprintf(stderr, "family-native 0.1.0: native SDL2/GLES2 Atlas ready; OK sets "
                  "destination; arrows move cursor; +/- zoom; Back exits\n");
  while (running) {
    uint64_t now = SDL_GetPerformanceCounter();
    float realdt =
        (float)((double)(now - last) / SDL_GetPerformanceFrequency());
    last = now;
    float dt = fminf(realdt, 0.05f);
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
      switch (event.type) {
      case SDL_QUIT:
        running = 0;
        break;
      case SDL_WINDOWEVENT:
        switch (event.window.event) {
        case SDL_WINDOWEVENT_HIDDEN:
        case SDL_WINDOWEVENT_MINIMIZED:
        case SDL_WINDOWEVENT_FOCUS_LOST:
          active = 0;
          break;
        case SDL_WINDOWEVENT_SHOWN:
        case SDL_WINDOWEVENT_RESTORED:
        case SDL_WINDOWEVENT_FOCUS_GAINED:
          active = 1;
          break;
        case SDL_WINDOWEVENT_SIZE_CHANGED:
          viewport(window);
          break;
        case SDL_WINDOWEVENT_CLOSE:
          running = 0;
          break;
        default:
          break;
        }
        break;
      case SDL_MOUSEMOTION:
        cursorx = clamp((float)event.motion.x, 0, W);
        cursory = clamp((float)event.motion.y, 0, H);
        break;
      case SDL_MOUSEBUTTONDOWN:
        if (event.button.button == SDL_BUTTON_LEFT) {
          cursorx = clamp((float)event.button.x, 0, W);
          cursory = clamp((float)event.button.y, 0, H);
          tx = clamp(cx + (cursorx - W / 2) / zoom, 0, 1536);
          ty = clamp(cy + (cursory - H / 2) / zoom, 0, 1024);
        }
        break;
      case SDL_KEYDOWN:
        switch (event.key.keysym.sym) {
        case SDLK_ESCAPE:
        case SDLK_AC_BACK:
          running = 0;
          break;
        case SDLK_RETURN:
        case SDLK_KP_ENTER:
          tx = clamp(cx + (cursorx - W / 2) / zoom, 0, 1536);
          ty = clamp(cy + (cursory - H / 2) / zoom, 0, 1024);
          break;
        case SDLK_LEFT:
          cursorx = clamp(cursorx - 40, 20, W - 20);
          break;
        case SDLK_RIGHT:
          cursorx = clamp(cursorx + 40, 20, W - 20);
          break;
        case SDLK_UP:
          cursory = clamp(cursory - 40, 20, H - 20);
          break;
        case SDLK_DOWN:
          cursory = clamp(cursory + 40, 20, H - 20);
          break;
        case SDLK_PLUS:
        case SDLK_EQUALS:
          zoom = clamp(zoom * 1.15f, .9f, 4);
          break;
        case SDLK_MINUS:
          zoom = clamp(zoom / 1.15f, .9f, 4);
          break;
        default:
          break;
        }
        break;
      case SDL_MOUSEWHEEL:
        zoom = clamp(zoom * powf(1.12f, (float)event.wheel.y), .9f, 4);
        break;
      default:
        break;
      }
    }
    if (!running)
      break;
    if (!active) {
      SDL_Delay(50);
      continue;
    }
    float dx = tx - px, dy = ty - py, dist = hypotf(dx, dy);
    int moving = dist > 0.5f;
    if (moving) {
      float step = fminf(44 * dt, dist);
      px += dx / dist * step;
      py += dy / dist * step;
      float angle = atan2f(dy, dx) * 180 / 3.14159265f;
      if (angle < 0)
        angle += 360;
      direction = ((int)floorf((angle + 22.5f) / 45)) % 8;
      animation += dt;
      frame = ((int)(animation * 24)) % 24;
    } else {
      animation = 0;
      frame = 0;
    }
    float blend = 1 - expf(-dt * 3.5f);
    cx += (px - cx) * blend;
    cy += (py - cy) * blend;
    float hw = W / zoom / 2, hh = H / zoom / 2;
    cx = hw >= 768 ? 768 : clamp(cx, hw, 1536 - hw);
    cy = hh >= 512 ? 512 : clamp(cy, hh, 1024 - hh);
    glClearColor(.08f, .13f, .11f, 1);
    glClear(GL_COLOR_BUFFER_BIT);
    quad(map, W / 2 - cx * zoom, H / 2 - cy * zoom, 1536 * zoom, 1024 * zoom, 0,
         0, 1, 1, 1, 1, 1, 1);
    float markerx = W / 2 + (tx - cx) * zoom,
          markery = H / 2 + (ty - cy) * zoom;
    quad(white, markerx - 11, markery - 2, 22, 4, 0, 0, 1, 1, 1, .85f, .2f,
         .85f);
    quad(white, markerx - 2, markery - 11, 4, 22, 0, 0, 1, 1, 1, .85f, .2f,
         .85f);
    float s = .5114155251f * zoom;
    quad(walk[direction], W / 2 + (px - cx) * zoom - 119.5f * s,
         H / 2 + (py - cy) * zoom - 114 * s, 240 * s, 135 * s,
         (frame % 6) / 6.0f, (frame / 6) / 4.0f, 1 / 6.0f, 1 / 4.0f, 1, 1, 1,
         1);
    quad(white, cursorx - 9, cursory - 1, 18, 2, 0, 0, 1, 1, 1, 1, 1, .9f);
    quad(white, cursorx - 1, cursory - 9, 2, 18, 0, 0, 1, 1, 1, 1, 1, .9f);
    SDL_GL_SwapWindow(window);
    frames++;
    elapsed += realdt;
    report += realdt;
    if (report >= 10) {
      fprintf(stderr,
              "family-native rendered=%llu active_seconds=%.1f; device timing "
              "is measured after deployment\n",
              (unsigned long long)frames, elapsed);
      report = 0;
    }
  }
  glDeleteTextures(1, &map);
  glDeleteTextures(8, walk);
  glDeleteTextures(1, &white);
  glDeleteBuffers(1, &vbo);
  glDeleteProgram(program);
  glDeleteShader(vertex);
  glDeleteShader(fragment);
  SDL_GL_DeleteContext(context);
  SDL_DestroyWindow(window);
  SDL_Quit();
  return 0;
}
