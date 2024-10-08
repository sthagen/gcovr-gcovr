#include <iostream>

void foo(int param) {
  if (param) {
     std::cout << "param is true" << std::endl; // GCOVR_EXCL_LINE
  } else {
     std::cout << "param is false" << std::endl;
  }
  // LCOV_EXCL_START
  if (param) {
     std::cout << "param is true" << std::endl;
  } else {
     std::cout << "param is false" << std::endl;
  }
  // LCOV_EXCL_STOP
}

void bar(int param) {  // GCOVR_EXCL_FUNCTION
  if (param) {
     std::cout << "param is true" << std::endl;
  } else {
     std::cout << "param is false" << std::endl;
  }
}

int main(int argc, char* argv[]) {
  foo(argc-1);
  bar(argc-1);
  return 0;
}
