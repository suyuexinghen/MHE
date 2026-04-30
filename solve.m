% Standalone Octave benchmark solve script for case: sinc-values
% Expected metrics:
%   max_abs_error <= 1e-12
%   elapsed_seconds

tic;

points = [0, 0.5, 1];
expected = [1, 2 / pi, 0];
computed = sinc(points);
max_abs_error = max(abs(computed - expected));
elapsed_seconds = toc;

fprintf('case_id: sinc-values\n');
fprintf('points: [%g, %g, %g]\n', points(1), points(2), points(3));
fprintf('computed: [%.17g, %.17g, %.17g]\n', computed(1), computed(2), computed(3));
fprintf('expected: [%.17g, %.17g, %.17g]\n', expected(1), expected(2), expected(3));
fprintf('max_abs_error: %.17g\n', max_abs_error);
fprintf('elapsed_seconds: %.17g\n', elapsed_seconds);

if max_abs_error > 1e-12
    error('sinc-values benchmark failed: max_abs_error %.17g exceeds tolerance 1e-12', max_abs_error);
end
